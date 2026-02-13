"""Tests for system notification service (Session 36)."""

import time

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.tgbot.notifications import SystemNotifier, get_admin_chat_id


def _make_notifier(admin_chat_id: str = "123456") -> SystemNotifier:
    """Create a SystemNotifier with a mocked bot."""
    bot = MagicMock()
    bot.send_message = AsyncMock()
    return SystemNotifier(bot=bot, admin_chat_id=admin_chat_id)


# ─── notify_api_error ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_notify_api_error_sends_message():
    """API error alert is sent to admin channel."""
    notifier = _make_notifier()
    await notifier.notify_api_error("/api/oracle/reading", 500, "Internal Server Error")

    notifier._bot.send_message.assert_called_once()
    call_kwargs = notifier._bot.send_message.call_args[1]
    assert call_kwargs["chat_id"] == "123456"
    assert "API Error" in call_kwargs["text"]
    assert "500" in call_kwargs["text"]


@pytest.mark.asyncio
async def test_notify_api_error_cooldown():
    """Duplicate alerts suppressed within 5-min window."""
    notifier = _make_notifier()
    await notifier.notify_api_error("/api/test", 500, "Error")
    await notifier.notify_api_error("/api/test", 500, "Error again")

    # Only first call should send
    assert notifier._bot.send_message.call_count == 1


@pytest.mark.asyncio
async def test_notify_api_error_different_endpoints():
    """Different endpoints have separate cooldowns."""
    notifier = _make_notifier()
    await notifier.notify_api_error("/api/a", 500, "Error")
    await notifier.notify_api_error("/api/b", 500, "Error")

    assert notifier._bot.send_message.call_count == 2


# ─── notify_high_error_rate ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_notify_high_error_rate_sends_alert():
    """High error rate triggers admin alert."""
    notifier = _make_notifier()
    await notifier.notify_high_error_rate(7.2, 15)

    call_kwargs = notifier._bot.send_message.call_args[1]
    assert "High Error Rate" in call_kwargs["text"]
    assert "7.2%" in call_kwargs["text"]


@pytest.mark.asyncio
async def test_notify_high_error_rate_cooldown():
    """High error rate cooldown prevents spam."""
    notifier = _make_notifier()
    await notifier.notify_high_error_rate(7.2, 15)
    await notifier.notify_high_error_rate(8.0, 15)

    assert notifier._bot.send_message.call_count == 1


# ─── notify_new_user ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_notify_new_user_sends_message():
    """New user registration sends notification."""
    notifier = _make_notifier()
    await notifier.notify_new_user("John Doe", "42")

    call_kwargs = notifier._bot.send_message.call_args[1]
    assert "New User Registered" in call_kwargs["text"]
    assert "John Doe" in call_kwargs["text"]
    assert "#42" in call_kwargs["text"]


# ─── notify_startup / shutdown ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_notify_startup_sends_message():
    """Service startup sends notification."""
    notifier = _make_notifier()
    await notifier.notify_startup("API Gateway", "1.0.0")

    call_kwargs = notifier._bot.send_message.call_args[1]
    assert "Service Started" in call_kwargs["text"]
    assert "API Gateway" in call_kwargs["text"]


@pytest.mark.asyncio
async def test_notify_shutdown_sends_message():
    """Service shutdown sends notification."""
    notifier = _make_notifier()
    await notifier.notify_shutdown("API Gateway", "SIGTERM")

    call_kwargs = notifier._bot.send_message.call_args[1]
    assert "Service Stopped" in call_kwargs["text"]
    assert "SIGTERM" in call_kwargs["text"]


# ─── notify_reading_milestone ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_notify_reading_milestone_sends_message():
    """Reading milestone sends notification."""
    notifier = _make_notifier()
    await notifier.notify_reading_milestone(1000)

    call_kwargs = notifier._bot.send_message.call_args[1]
    assert "Reading Milestone" in call_kwargs["text"]
    assert "1,000" in call_kwargs["text"]


# ─── Graceful degradation ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_graceful_degradation_no_chat_id():
    """Missing chat ID logs warning, no crash."""
    notifier = _make_notifier(admin_chat_id="")
    await notifier.notify_startup("test", "1.0.0")

    # send_message should not be called
    notifier._bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_graceful_degradation_bot_error():
    """Bot error doesn't crash the notifier."""
    from telegram.error import TelegramError

    notifier = _make_notifier()
    notifier._bot.send_message = AsyncMock(side_effect=TelegramError("Bot blocked"))
    # Should not raise
    await notifier.notify_startup("test", "1.0.0")


# ─── Cooldown expiry ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cooldown_expires_after_window():
    """Alerts resume after cooldown window passes."""
    notifier = _make_notifier()

    # First call succeeds
    await notifier.notify_api_error("/api/test", 500, "Error")
    assert notifier._bot.send_message.call_count == 1

    # Manually expire the cooldown
    for key in notifier._cooldowns:
        notifier._cooldowns[key] = time.monotonic() - 400  # 400s > 300s cooldown

    # Second call should now succeed
    await notifier.notify_api_error("/api/test", 500, "Error again")
    assert notifier._bot.send_message.call_count == 2


# ─── get_admin_chat_id ───────────────────────────────────────────────────────


def test_get_admin_chat_id_from_env():
    """get_admin_chat_id reads NPS_ADMIN_CHAT_ID first."""
    with patch.dict("os.environ", {"NPS_ADMIN_CHAT_ID": "999", "NPS_CHAT_ID": "111"}):
        assert get_admin_chat_id() == "999"


def test_get_admin_chat_id_fallback():
    """get_admin_chat_id falls back to NPS_CHAT_ID."""
    with patch.dict(
        "os.environ", {"NPS_ADMIN_CHAT_ID": "", "NPS_CHAT_ID": "111"}, clear=False
    ):
        result = get_admin_chat_id()
        assert result == "111"
