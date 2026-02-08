"""Tests for location endpoints."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.location_service import LocationService, reset_caches

COORDINATES_URL = "/api/location/coordinates"
DETECT_URL = "/api/location/detect"


@pytest.fixture(autouse=True)
def _reset_location_caches():
    """Reset location caches before each test."""
    reset_caches()
    yield
    reset_caches()


def _mock_nominatim_success():
    """Create a mock httpx response for successful Nominatim lookup."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "lat": "35.6892",
            "lon": "51.3890",
            "display_name": "Tehran, Tehran Province, Iran",
        }
    ]
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def _mock_nominatim_empty():
    """Create a mock httpx response for city not found."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = []
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def _mock_ipapi_success():
    """Create a mock httpx response for successful IP lookup."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "ip": "8.8.8.8",
        "city": "Mountain View",
        "country_name": "United States",
        "country_code": "US",
        "latitude": 37.386,
        "longitude": -122.0838,
        "timezone": "America/Los_Angeles",
    }
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# ─── GET /coordinates ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_coordinates_success(client):
    mock_resp = _mock_nominatim_success()
    with patch("app.services.location_service.httpx.Client") as MockClient:
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_resp
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        MockClient.return_value = mock_client_instance

        resp = await client.get(COORDINATES_URL, params={"city": "Tehran"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["city"] == "Tehran"
        assert data["latitude"] == 35.6892
        assert data["longitude"] == 51.389
        assert data["cached"] is False


@pytest.mark.asyncio
async def test_coordinates_with_country(client):
    mock_resp = _mock_nominatim_success()
    with patch("app.services.location_service.httpx.Client") as MockClient:
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_resp
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        MockClient.return_value = mock_client_instance

        resp = await client.get(
            COORDINATES_URL, params={"city": "Tehran", "country": "Iran"}
        )
        assert resp.status_code == 200
        assert resp.json()["country"] == "Iran"


@pytest.mark.asyncio
async def test_coordinates_city_not_found_404(client):
    mock_resp = _mock_nominatim_empty()
    with patch("app.services.location_service.httpx.Client") as MockClient:
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_resp
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        MockClient.return_value = mock_client_instance

        resp = await client.get(COORDINATES_URL, params={"city": "Nonexistentville"})
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_coordinates_service_error(client):
    import httpx as httpx_mod

    with patch("app.services.location_service.httpx.Client") as MockClient:
        mock_client_instance = MagicMock()
        mock_client_instance.get.side_effect = httpx_mod.ConnectError("timeout")
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        MockClient.return_value = mock_client_instance

        resp = await client.get(COORDINATES_URL, params={"city": "Tehran"})
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_coordinates_cache_second_call(client):
    mock_resp = _mock_nominatim_success()
    with patch("app.services.location_service.httpx.Client") as MockClient:
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_resp
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        MockClient.return_value = mock_client_instance

        resp1 = await client.get(COORDINATES_URL, params={"city": "Tehran"})
        assert resp1.status_code == 200
        assert resp1.json()["cached"] is False

        resp2 = await client.get(COORDINATES_URL, params={"city": "Tehran"})
        assert resp2.status_code == 200
        assert resp2.json()["cached"] is True


@pytest.mark.asyncio
async def test_coordinates_missing_city_422(client):
    resp = await client.get(COORDINATES_URL)
    assert resp.status_code == 422


# ─── GET /detect ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_detect_local_ip_400(client):
    """Testclient IP is 'testclient' — should return 400."""
    resp = await client.get(DETECT_URL)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_detect_ipapi_success(client):
    mock_resp = _mock_ipapi_success()
    with (
        patch("app.services.location_service.httpx.Client") as MockClient,
        patch("app.routers.location._LOCAL_IPS", set()),
    ):
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_resp
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        MockClient.return_value = mock_client_instance

        resp = await client.get(DETECT_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["city"] == "Mountain View"
        assert data["country"] == "United States"
        assert data["timezone"] == "America/Los_Angeles"


@pytest.mark.asyncio
async def test_detect_ipapi_error_502(client):
    import httpx as httpx_mod

    with (
        patch("app.services.location_service.httpx.Client") as MockClient,
        patch("app.routers.location._LOCAL_IPS", set()),
    ):
        mock_client_instance = MagicMock()
        mock_client_instance.get.side_effect = httpx_mod.ConnectError("fail")
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        MockClient.return_value = mock_client_instance

        resp = await client.get(DETECT_URL)
        assert resp.status_code == 502


@pytest.mark.asyncio
async def test_detect_cache_second_call(client):
    mock_resp = _mock_ipapi_success()
    with (
        patch("app.services.location_service.httpx.Client") as MockClient,
        patch("app.routers.location._LOCAL_IPS", set()),
    ):
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_resp
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        MockClient.return_value = mock_client_instance

        resp1 = await client.get(DETECT_URL)
        assert resp1.status_code == 200
        assert resp1.json()["cached"] is False

        resp2 = await client.get(DETECT_URL)
        assert resp2.status_code == 200
        assert resp2.json()["cached"] is True


# ─── Auth ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_coordinates_readonly_allowed(readonly_client):
    mock_resp = _mock_nominatim_success()
    with patch("app.services.location_service.httpx.Client") as MockClient:
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_resp
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        MockClient.return_value = mock_client_instance

        resp = await readonly_client.get(COORDINATES_URL, params={"city": "Tehran"})
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_coordinates_unauthenticated_401(unauth_client):
    resp = await unauth_client.get(COORDINATES_URL, params={"city": "Tehran"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_detect_readonly_allowed(readonly_client):
    """Readonly can access detect, but will get 400 due to testclient IP."""
    resp = await readonly_client.get(DETECT_URL)
    assert resp.status_code == 400
