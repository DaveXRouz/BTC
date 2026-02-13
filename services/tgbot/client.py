"""Async HTTP client for NPS API communication."""

import logging

import httpx

from . import config

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


async def get_client() -> httpx.AsyncClient:
    """Get or create the shared httpx async client."""
    global _client  # noqa: PLW0603
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=config.API_BASE_URL,
            timeout=httpx.Timeout(10.0, connect=5.0),
            headers={"Authorization": f"Bearer {config.BOT_SERVICE_KEY}"},
        )
    return _client


async def close_client() -> None:
    """Close the shared httpx client."""
    global _client  # noqa: PLW0603
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None


async def link_account(chat_id: int, username: str | None, api_key: str) -> dict | None:
    """Call POST /telegram/link to associate a Telegram chat with an NPS user."""
    client = await get_client()
    try:
        resp = await client.post(
            "/telegram/link",
            json={
                "telegram_chat_id": chat_id,
                "telegram_username": username,
                "api_key": api_key,
            },
        )
        if resp.status_code == 200:
            return resp.json()
        logger.warning("Link failed: %d %s", resp.status_code, resp.text)
        return None
    except httpx.HTTPError as exc:
        logger.error("API link_account error: %s", exc)
        return None


async def get_status(chat_id: int) -> dict | None:
    """Call GET /telegram/status/{chat_id} to get link info."""
    client = await get_client()
    try:
        resp = await client.get(f"/telegram/status/{chat_id}")
        if resp.status_code == 200:
            return resp.json()
        return None
    except httpx.HTTPError as exc:
        logger.error("API get_status error: %s", exc)
        return None


async def get_profile(chat_id: int) -> list[dict]:
    """Call GET /telegram/profile/{chat_id} to get Oracle profiles."""
    client = await get_client()
    try:
        resp = await client.get(f"/telegram/profile/{chat_id}")
        if resp.status_code == 200:
            return resp.json()
        return []
    except httpx.HTTPError as exc:
        logger.error("API get_profile error: %s", exc)
        return []
