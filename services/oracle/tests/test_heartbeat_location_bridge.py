"""Tests for heartbeat and location data flow through the framework bridge."""

from oracle_service.framework_bridge import (
    generate_single_reading,
    map_oracle_user_to_framework_kwargs,
)


class TestHeartbeatBridge:
    """Verify heartbeat data passes through bridge to framework."""

    def test_actual_bpm_passed_to_framework(self) -> None:
        result = generate_single_reading(
            full_name="Test User",
            birth_day=15,
            birth_month=6,
            birth_year=1990,
            heart_rate_bpm=72,
        )
        heartbeat = result.get("heartbeat", {})
        assert heartbeat is not None
        assert heartbeat.get("bpm") == 72
        assert heartbeat.get("bpm_source") == "actual"

    def test_missing_bpm_uses_estimated(self) -> None:
        result = generate_single_reading(
            full_name="Test User",
            birth_day=15,
            birth_month=6,
            birth_year=1990,
        )
        heartbeat = result.get("heartbeat", {})
        assert heartbeat is not None
        assert heartbeat.get("bpm_source") == "estimated"
        assert heartbeat.get("bpm", 0) > 0

    def test_bpm_element_mapping(self) -> None:
        result = generate_single_reading(
            full_name="Test User",
            birth_day=15,
            birth_month=6,
            birth_year=1990,
            heart_rate_bpm=72,
        )
        heartbeat = result.get("heartbeat", {})
        element = heartbeat.get("element", "")
        assert element in ("Wood", "Fire", "Earth", "Metal", "Water")

    def test_bpm_lifetime_beats_positive(self) -> None:
        result = generate_single_reading(
            full_name="Test User",
            birth_day=15,
            birth_month=6,
            birth_year=1990,
            heart_rate_bpm=72,
        )
        heartbeat = result.get("heartbeat", {})
        assert heartbeat.get("total_lifetime_beats", 0) > 0


class TestLocationBridge:
    """Verify location data passes through bridge to framework."""

    def test_coordinates_produce_location_data(self) -> None:
        result = generate_single_reading(
            full_name="Test User",
            birth_day=15,
            birth_month=6,
            birth_year=1990,
            latitude=40.7,
            longitude=-74.0,
        )
        location = result.get("location")
        assert location is not None
        assert location.get("element") in ("Wood", "Fire", "Earth", "Metal", "Water")

    def test_missing_coordinates_returns_none(self) -> None:
        result = generate_single_reading(
            full_name="Test User",
            birth_day=15,
            birth_month=6,
            birth_year=1990,
        )
        location = result.get("location")
        assert location is None

    def test_location_element_mapping(self) -> None:
        # NYC (40.7N)
        nyc = generate_single_reading(
            full_name="Test",
            birth_day=1,
            birth_month=1,
            birth_year=2000,
            latitude=40.7,
            longitude=-74.0,
        )
        nyc_element = nyc.get("location", {}).get("element", "")
        assert nyc_element in ("Wood", "Fire", "Earth", "Metal", "Water")

        # Cairo (30.0N)
        cairo = generate_single_reading(
            full_name="Test",
            birth_day=1,
            birth_month=1,
            birth_year=2000,
            latitude=30.0,
            longitude=31.2,
        )
        cairo_element = cairo.get("location", {}).get("element", "")
        assert cairo_element in ("Wood", "Fire", "Earth", "Metal", "Water")


class TestConfidenceBridge:
    """Verify confidence scoring includes heartbeat/location boosts."""

    def test_confidence_with_all_optional_data(self) -> None:
        result = generate_single_reading(
            full_name="Test User",
            birth_day=15,
            birth_month=6,
            birth_year=1990,
            mother_name="Mother",
            gender="male",
            heart_rate_bpm=72,
            latitude=40.7,
            longitude=-74.0,
        )
        conf = result.get("confidence", {})
        assert conf.get("score", 0) > 50

    def test_confidence_without_optional_data(self) -> None:
        result = generate_single_reading(
            full_name="Test User",
            birth_day=15,
            birth_month=6,
            birth_year=1990,
        )
        conf = result.get("confidence", {})
        assert conf.get("score", 0) >= 50

    def test_confidence_partial_optional_data(self) -> None:
        minimal = generate_single_reading(
            full_name="Test User",
            birth_day=15,
            birth_month=6,
            birth_year=1990,
        )
        with_location = generate_single_reading(
            full_name="Test User",
            birth_day=15,
            birth_month=6,
            birth_year=1990,
            latitude=40.7,
            longitude=-74.0,
        )
        minimal_score = minimal.get("confidence", {}).get("score", 0)
        location_score = with_location.get("confidence", {}).get("score", 0)
        # Location should boost confidence
        assert location_score >= minimal_score


class TestFieldMapping:
    """Verify map_oracle_user_to_framework_kwargs handles all fields."""

    def test_map_dict_with_all_fields(self) -> None:
        user = {
            "name": "Test User",
            "birthday": "1990-06-15",
            "mother_name": "Mother",
            "gender": "female",
            "heart_rate_bpm": 65,
            "latitude": 35.7,
            "longitude": 51.4,
            "timezone_hours": 4,
            "timezone_minutes": 30,
        }
        kwargs = map_oracle_user_to_framework_kwargs(user)
        assert kwargs["full_name"] == "Test User"
        assert kwargs["birth_day"] == 15
        assert kwargs["birth_month"] == 6
        assert kwargs["birth_year"] == 1990
        assert kwargs["mother_name"] == "Mother"
        assert kwargs["gender"] == "female"
        assert kwargs["heart_rate_bpm"] == 65
        assert kwargs["latitude"] == 35.7
        assert kwargs["longitude"] == 51.4
        assert kwargs["tz_hours"] == 4
        assert kwargs["tz_minutes"] == 30

    def test_map_dict_minimal_fields(self) -> None:
        user = {
            "name": "Test",
            "birthday": "2000-01-01",
            "mother_name": None,
        }
        kwargs = map_oracle_user_to_framework_kwargs(user)
        assert kwargs["full_name"] == "Test"
        assert kwargs["heart_rate_bpm"] is None
        assert kwargs["latitude"] is None
        assert kwargs["gender"] is None
        assert kwargs["tz_hours"] == 0
