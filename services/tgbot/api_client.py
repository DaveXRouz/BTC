"""Per-user HTTP client for bot → NPS API communication.

Unlike the shared client in client.py (which uses the bot service key),
this module creates per-user clients using their linked API keys.
This is used by reading commands that need to act on behalf of a user.
"""

import logging
from dataclasses import dataclass

import httpx

from . import config

logger = logging.getLogger(__name__)

API_TIMEOUT = 30.0  # Readings with AI can take time


@dataclass
class APIResponse:
    """Standardized response from the NPS API."""

    success: bool
    data: dict | None = None
    error: str | None = None
    status_code: int = 0


class NPSAPIClient:
    """Async HTTP client that authenticates as a specific NPS user."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=config.API_BASE_URL,
            timeout=httpx.Timeout(API_TIMEOUT, connect=5.0),
            headers={"Authorization": f"Bearer {api_key}"},
        )

    async def _request(
        self,
        method: str,
        url: str,
        json: dict | None = None,
        params: dict | None = None,
    ) -> APIResponse:
        """Execute an API request and return a standardized response."""
        try:
            resp = await self._client.request(method, url, json=json, params=params)
            if resp.status_code == 200 or resp.status_code == 201:
                return APIResponse(
                    success=True,
                    data=resp.json(),
                    status_code=resp.status_code,
                )
            if resp.status_code == 401:
                return APIResponse(
                    success=False,
                    error="Your API key is no longer valid. Re-link with /link",
                    status_code=401,
                )
            if resp.status_code == 429:
                return APIResponse(
                    success=False,
                    error="Too many requests. Wait a minute and try again.",
                    status_code=429,
                )
            return APIResponse(
                success=False,
                error=f"Server error ({resp.status_code})",
                status_code=resp.status_code,
            )
        except httpx.TimeoutException:
            logger.warning("API timeout for %s %s", method, url)
            return APIResponse(
                success=False,
                error="Reading took too long. Try again in a moment.",
                status_code=0,
            )
        except httpx.HTTPError as exc:
            logger.error("API HTTP error: %s", exc)
            return APIResponse(
                success=False,
                error="Could not reach the server. Try again later.",
                status_code=0,
            )

    async def create_reading(self, datetime_str: str | None = None) -> APIResponse:
        """POST /oracle/reading — full time-based oracle reading."""
        body: dict = {}
        if datetime_str:
            body["datetime"] = datetime_str
        return await self._request("POST", "/oracle/reading", json=body)

    async def create_question(self, question: str) -> APIResponse:
        """POST /oracle/question — question reading."""
        return await self._request(
            "POST", "/oracle/question", json={"question": question}
        )

    async def create_name_reading(self, name: str) -> APIResponse:
        """POST /oracle/name — name analysis reading."""
        return await self._request("POST", "/oracle/name", json={"name": name})

    async def get_daily(self, date: str | None = None) -> APIResponse:
        """GET /oracle/daily — daily insight."""
        params: dict = {}
        if date:
            params["date"] = date
        return await self._request("GET", "/oracle/daily", params=params)

    async def list_readings(self, limit: int = 5, offset: int = 0) -> APIResponse:
        """GET /oracle/readings — reading history."""
        return await self._request(
            "GET", "/oracle/readings", params={"limit": limit, "offset": offset}
        )

    async def get_reading(self, reading_id: int) -> APIResponse:
        """GET /oracle/readings/{id} — single reading detail."""
        return await self._request("GET", f"/oracle/readings/{reading_id}")

    async def close(self) -> None:
        """Close the underlying httpx client."""
        await self._client.aclose()
