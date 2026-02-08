"""Location service — geocoding via Nominatim + IP detection via ipapi.co."""

import logging
import threading
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_USER_AGENT = "NPS-V4-Oracle/4.0"
_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_IPAPI_URL = "https://ipapi.co/{ip}/json/"

# ─── Caches ─────────────────────────────────────────────────────────────────

_CITY_CACHE_TTL = 30 * 86400  # 30 days
_IP_CACHE_TTL = 7 * 86400  # 7 days

_city_cache: dict[str, dict[str, Any]] = {}
_ip_cache: dict[str, dict[str, Any]] = {}
_cache_lock = threading.Lock()

# Rate limiting for Nominatim (1 req/sec)
_nominatim_lock = threading.Lock()
_last_nominatim_request = 0.0


def reset_caches() -> None:
    """Clear all location caches."""
    with _cache_lock:
        _city_cache.clear()
        _ip_cache.clear()


def _get_timezone(lat: float, lon: float) -> str | None:
    """Get timezone from coordinates using timezonefinder (optional dep)."""
    try:
        from timezonefinder import TimezoneFinder

        tf = TimezoneFinder()
        return tf.timezone_at(lat=lat, lng=lon)
    except ImportError:
        return None
    except Exception:
        return None


# ─── Location Service ───────────────────────────────────────────────────────


class LocationService:
    """Geocoding + IP-based location detection with caching."""

    def get_coordinates(self, city: str, country: str | None = None) -> dict | None:
        """Look up city coordinates via Nominatim.

        Returns dict with keys: city, country, latitude, longitude, timezone, cached.
        Returns None if city not found.
        """
        cache_key = f"{city}:{country or ''}"

        with _cache_lock:
            if cache_key in _city_cache:
                entry = _city_cache[cache_key]
                if time.monotonic() - entry["ts"] < _CITY_CACHE_TTL:
                    return {**entry["result"], "cached": True}
                del _city_cache[cache_key]

        # Rate limit Nominatim (1 req/sec)
        global _last_nominatim_request
        with _nominatim_lock:
            elapsed = time.monotonic() - _last_nominatim_request
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
            _last_nominatim_request = time.monotonic()

        query = city
        if country:
            query = f"{city}, {country}"

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    _NOMINATIM_URL,
                    params={"q": query, "format": "json", "limit": 1},
                    headers={"User-Agent": _USER_AGENT},
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError:
            logger.warning("Nominatim request failed for %s", query, exc_info=True)
            return None

        if not data:
            return None

        item = data[0]
        lat = float(item["lat"])
        lon = float(item["lon"])
        tz = _get_timezone(lat, lon)

        result = {
            "city": city,
            "country": (
                item.get("display_name", "").split(", ")[-1]
                if country is None
                else country
            ),
            "latitude": lat,
            "longitude": lon,
            "timezone": tz,
            "cached": False,
        }

        with _cache_lock:
            _city_cache[cache_key] = {"result": result, "ts": time.monotonic()}

        return result

    def detect_location(self, ip: str) -> dict | None:
        """Detect location from IP address via ipapi.co.

        Returns dict with keys: ip, city, country, country_code, latitude,
        longitude, timezone, cached.
        Returns None on failure.
        """
        with _cache_lock:
            if ip in _ip_cache:
                entry = _ip_cache[ip]
                if time.monotonic() - entry["ts"] < _IP_CACHE_TTL:
                    return {**entry["result"], "cached": True}
                del _ip_cache[ip]

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    _IPAPI_URL.format(ip=ip),
                    headers={"User-Agent": _USER_AGENT},
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError:
            logger.warning("ipapi.co request failed for %s", ip, exc_info=True)
            return None

        if data.get("error"):
            return None

        result = {
            "ip": ip,
            "city": data.get("city"),
            "country": data.get("country_name"),
            "country_code": data.get("country_code"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "timezone": data.get("timezone"),
            "cached": False,
        }

        with _cache_lock:
            _ip_cache[ip] = {"result": result, "ts": time.monotonic()}

        return result
