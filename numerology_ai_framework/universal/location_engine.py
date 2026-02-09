"""
Location Engine - Universal Tier Module 3
==========================================
Purpose: Encode geographic coordinates into elemental signatures
         Maps latitude zones to elements, hemispheres to polarity

Dependencies: None (pure stdlib)
"""

from typing import Dict


class LocationEngine:
    """Geographic coordinate encoder using elemental zone mapping."""

    # Latitude zones (absolute value): degrees → element
    LATITUDE_ZONES = [
        (15, "Fire"),
        (30, "Earth"),
        (45, "Metal"),
        (60, "Water"),
        (90, "Wood"),
    ]

    @staticmethod
    def latitude_element(lat: float) -> str:
        """Map absolute latitude to elemental zone."""
        abs_lat = abs(lat)
        for boundary, element in LocationEngine.LATITUDE_ZONES:
            if abs_lat <= boundary:
                return element
        return "Wood"  # 60-90°

    @staticmethod
    def hemisphere_polarity(lat: float, lon: float) -> Dict:
        """Determine polarity from hemisphere position."""
        ns = "Yang" if lat >= 0 else "Yin"
        ew = "Yang" if lon >= 0 else "Yin"
        return {
            "lat_hemisphere": "N" if lat >= 0 else "S",
            "lon_hemisphere": "E" if lon >= 0 else "W",
            "lat_polarity": ns,
            "lon_polarity": ew,
        }

    @staticmethod
    def timezone_estimate(lon: float) -> int:
        """Estimate UTC offset from longitude."""
        return round(lon / 15)

    @staticmethod
    def location_signature(lat: float, lon: float) -> Dict:
        """Generate complete encoded location signature."""
        element = LocationEngine.latitude_element(lat)
        polarity = LocationEngine.hemisphere_polarity(lat, lon)
        tz = LocationEngine.timezone_estimate(lon)

        return {
            "latitude": lat,
            "longitude": lon,
            "element": element,
            "timezone_estimate": tz,
            **polarity,
        }


# Test vectors
TEST_VECTORS = [
    # (city, lat, lon, expected_element, expected_tz)
    ("NYC", 40.7, -74.0, "Metal", -5),
    ("Tokyo", 35.7, 139.7, "Metal", 9),
    ("London", 51.5, -0.1, "Water", 0),
    ("Cairo", 30.0, 31.2, "Earth", 2),
    ("Sao Paulo", -23.5, -46.6, "Earth", -3),
]


if __name__ == "__main__":
    print("=" * 60)
    print("LOCATION ENGINE - SELF TEST")
    print("=" * 60)

    passed = 0
    failed = 0

    for city, lat, lon, exp_element, exp_tz in TEST_VECTORS:
        sig = LocationEngine.location_signature(lat, lon)
        element_ok = sig["element"] == exp_element
        tz_ok = sig["timezone_estimate"] == exp_tz

        if element_ok and tz_ok:
            print(
                f"✓ {city:12s}: {sig['element']:6s} TZ={sig['timezone_estimate']:+d} "
                f"({sig['lat_hemisphere']}/{sig['lon_hemisphere']})"
            )
            passed += 1
        else:
            print(
                f"✗ {city}: element={sig['element']}(exp {exp_element}) "
                f"tz={sig['timezone_estimate']}(exp {exp_tz})"
            )
            failed += 1

    # Edge case: equator
    eq = LocationEngine.location_signature(0.0, 0.0)
    if eq["element"] == "Fire" and eq["timezone_estimate"] == 0:
        print(f"✓ Equator/PM:  {eq['element']:6s} TZ={eq['timezone_estimate']:+d}")
        passed += 1
    else:
        print(f"✗ Equator: {eq}")
        failed += 1

    print(f"\n{passed} passed, {failed} failed")
    exit(0 if failed == 0 else 1)
