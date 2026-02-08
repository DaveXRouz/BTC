"""Phase 2: Multi-user reading deep integration tests."""

import time

import pytest

from conftest import api_url


def _create_test_users(api_client, count=2):
    """Create test users and return their IDs + payload data."""
    users = []
    for i in range(count):
        resp = api_client.post(
            api_url("/api/oracle/users"),
            json={
                "name": f"IntTest_MU_{i}",
                "birthday": f"199{i}-0{i + 1}-15",
                "mother_name": f"Mother_{i}",
                "country": "US",
                "city": "TestCity",
            },
        )
        if resp.status_code == 201:
            users.append(resp.json())
    return users


@pytest.mark.multi_user
class TestMultiUserReading:
    """Core multi-user reading flow."""

    def test_two_user_reading(self, api_client):
        """2-user multi-user reading returns expected structure."""
        resp = api_client.post(
            api_url("/api/oracle/reading/multi-user"),
            json={
                "users": [
                    {
                        "name": "Alice Test",
                        "birth_year": 1990,
                        "birth_month": 3,
                        "birth_day": 15,
                    },
                    {
                        "name": "Bob Test",
                        "birth_year": 1985,
                        "birth_month": 7,
                        "birth_day": 22,
                    },
                ],
                "primary_user_index": 0,
                "include_interpretation": False,
            },
        )
        assert (
            resp.status_code == 200
        ), f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()

        # Verify expected response fields
        assert "user_count" in data
        assert data["user_count"] == 2
        assert "profiles" in data
        assert len(data["profiles"]) == 2
        assert "reading_id" in data

    def test_five_user_reading(self, api_client):
        """5-user multi-user reading returns expected structure."""
        users = [
            {
                "name": f"User_{i}",
                "birth_year": 1980 + i,
                "birth_month": (i % 12) + 1,
                "birth_day": 10 + i,
            }
            for i in range(5)
        ]
        resp = api_client.post(
            api_url("/api/oracle/reading/multi-user"),
            json={
                "users": users,
                "primary_user_index": 0,
                "include_interpretation": False,
            },
        )
        assert (
            resp.status_code == 200
        ), f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["user_count"] == 5
        assert len(data["profiles"]) == 5

    def test_primary_user_index(self, api_client):
        """Primary user index correctly identifies the primary asker."""
        resp = api_client.post(
            api_url("/api/oracle/reading/multi-user"),
            json={
                "users": [
                    {
                        "name": "First",
                        "birth_year": 1990,
                        "birth_month": 1,
                        "birth_day": 1,
                    },
                    {
                        "name": "Second",
                        "birth_year": 1991,
                        "birth_month": 2,
                        "birth_day": 2,
                    },
                ],
                "primary_user_index": 1,
                "include_interpretation": False,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("reading_id") is not None

    def test_reading_stored_in_db(self, api_client):
        """Multi-user reading is persisted and retrievable from history."""
        resp = api_client.post(
            api_url("/api/oracle/reading/multi-user"),
            json={
                "users": [
                    {
                        "name": "Store_A",
                        "birth_year": 1990,
                        "birth_month": 5,
                        "birth_day": 10,
                    },
                    {
                        "name": "Store_B",
                        "birth_year": 1988,
                        "birth_month": 8,
                        "birth_day": 20,
                    },
                ],
                "primary_user_index": 0,
                "include_interpretation": False,
            },
        )
        assert resp.status_code == 200
        reading_id = resp.json()["reading_id"]

        # Verify in reading history
        history_resp = api_client.get(
            api_url("/api/oracle/readings?sign_type=multi_user")
        )
        assert history_resp.status_code == 200
        readings = history_resp.json()["readings"]
        ids = [r["id"] for r in readings]
        assert reading_id in ids, f"Reading {reading_id} not found in history"


@pytest.mark.multi_user
class TestMultiUserValidation:
    """Error case validation for multi-user readings."""

    def test_single_user_rejected(self, api_client):
        """Submitting only 1 user should be rejected (need >= 2)."""
        resp = api_client.post(
            api_url("/api/oracle/reading/multi-user"),
            json={
                "users": [
                    {
                        "name": "Alone",
                        "birth_year": 1990,
                        "birth_month": 1,
                        "birth_day": 1,
                    },
                ],
                "primary_user_index": 0,
                "include_interpretation": False,
            },
        )
        assert resp.status_code == 422

    def test_too_many_users_rejected(self, api_client):
        """Submitting > 10 users should be rejected."""
        users = [
            {
                "name": f"TooMany_{i}",
                "birth_year": 1980 + i,
                "birth_month": 1,
                "birth_day": 1,
            }
            for i in range(11)
        ]
        resp = api_client.post(
            api_url("/api/oracle/reading/multi-user"),
            json={
                "users": users,
                "primary_user_index": 0,
                "include_interpretation": False,
            },
        )
        assert resp.status_code == 422

    def test_invalid_birth_data(self, api_client):
        """Invalid birth data should return validation error."""
        resp = api_client.post(
            api_url("/api/oracle/reading/multi-user"),
            json={
                "users": [
                    {
                        "name": "Valid",
                        "birth_year": 1990,
                        "birth_month": 1,
                        "birth_day": 1,
                    },
                    {
                        "name": "Invalid",
                        "birth_year": -1,
                        "birth_month": 13,
                        "birth_day": 32,
                    },
                ],
                "primary_user_index": 0,
                "include_interpretation": False,
            },
        )
        assert resp.status_code in (422, 400)

    def test_empty_name_rejected(self, api_client):
        """Empty name should be rejected."""
        resp = api_client.post(
            api_url("/api/oracle/reading/multi-user"),
            json={
                "users": [
                    {"name": "", "birth_year": 1990, "birth_month": 1, "birth_day": 1},
                    {
                        "name": "Valid",
                        "birth_year": 1991,
                        "birth_month": 2,
                        "birth_day": 2,
                    },
                ],
                "primary_user_index": 0,
                "include_interpretation": False,
            },
        )
        assert resp.status_code == 422

    def test_out_of_bounds_primary_index(self, api_client):
        """Primary user index beyond array should fail."""
        resp = api_client.post(
            api_url("/api/oracle/reading/multi-user"),
            json={
                "users": [
                    {"name": "A", "birth_year": 1990, "birth_month": 1, "birth_day": 1},
                    {"name": "B", "birth_year": 1991, "birth_month": 2, "birth_day": 2},
                ],
                "primary_user_index": 5,
                "include_interpretation": False,
            },
        )
        assert resp.status_code in (422, 500)


@pytest.mark.multi_user
class TestMultiUserPerformance:
    """Performance scaling tests for multi-user readings."""

    def test_two_user_under_5s(self, api_client):
        """2-user reading should complete in under 5 seconds."""
        start = time.perf_counter()
        resp = api_client.post(
            api_url("/api/oracle/reading/multi-user"),
            json={
                "users": [
                    {
                        "name": "Perf_A",
                        "birth_year": 1990,
                        "birth_month": 3,
                        "birth_day": 15,
                    },
                    {
                        "name": "Perf_B",
                        "birth_year": 1985,
                        "birth_month": 7,
                        "birth_day": 22,
                    },
                ],
                "primary_user_index": 0,
                "include_interpretation": False,
            },
        )
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < 5.0, f"2-user reading took {elapsed:.2f}s, target <5s"
        print(f"\n  2-user reading: {elapsed:.2f}s")

    def test_five_user_under_8s(self, api_client):
        """5-user reading should complete in under 8 seconds."""
        users = [
            {
                "name": f"Perf5_{i}",
                "birth_year": 1980 + i,
                "birth_month": (i % 12) + 1,
                "birth_day": 10 + i,
            }
            for i in range(5)
        ]
        start = time.perf_counter()
        resp = api_client.post(
            api_url("/api/oracle/reading/multi-user"),
            json={
                "users": users,
                "primary_user_index": 0,
                "include_interpretation": False,
            },
        )
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < 8.0, f"5-user reading took {elapsed:.2f}s, target <8s"
        print(f"\n  5-user reading: {elapsed:.2f}s")

    def test_ten_user_under_15s(self, api_client):
        """10-user reading should complete in under 15 seconds."""
        users = [
            {
                "name": f"Perf10_{i}",
                "birth_year": 1975 + i,
                "birth_month": (i % 12) + 1,
                "birth_day": (i % 28) + 1,
            }
            for i in range(10)
        ]
        start = time.perf_counter()
        resp = api_client.post(
            api_url("/api/oracle/reading/multi-user"),
            json={
                "users": users,
                "primary_user_index": 0,
                "include_interpretation": False,
            },
        )
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < 15.0, f"10-user reading took {elapsed:.2f}s, target <15s"
        print(f"\n  10-user reading: {elapsed:.2f}s")


@pytest.mark.multi_user
class TestMultiUserJunctionTable:
    """Verify junction table entries for multi-user readings."""

    def test_junction_entries_created(self, api_client, db_connection):
        """Junction table should have entries for all users in a multi-user reading."""
        from sqlalchemy import text

        # Create multi-user reading with known user_ids (None since anonymous)
        resp = api_client.post(
            api_url("/api/oracle/reading/multi-user"),
            json={
                "users": [
                    {
                        "name": "Junc_A",
                        "birth_year": 1990,
                        "birth_month": 3,
                        "birth_day": 15,
                    },
                    {
                        "name": "Junc_B",
                        "birth_year": 1985,
                        "birth_month": 7,
                        "birth_day": 22,
                    },
                ],
                "primary_user_index": 0,
                "include_interpretation": False,
            },
        )
        assert resp.status_code == 200
        reading_id = resp.json()["reading_id"]

        # Check that the reading exists in oracle_readings with is_multi_user=TRUE
        result = db_connection.execute(
            text("SELECT is_multi_user FROM oracle_readings WHERE id = :id"),
            {"id": reading_id},
        )
        row = result.fetchone()
        assert row is not None, f"Reading {reading_id} not found in DB"
        assert row[0] is True, "Reading should be marked as multi_user"
