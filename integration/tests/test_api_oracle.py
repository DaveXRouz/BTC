"""Phase 3.2: API Oracle endpoint integration tests — CRUD, readings, encryption."""

import pytest
from sqlalchemy import text

from conftest import api_url


@pytest.mark.api
class TestOracleUserCRUD:
    """Test Oracle user management endpoints."""

    def test_create_user(self, api_client):
        """POST /api/oracle/users creates a user and returns 201."""
        resp = api_client.post(
            api_url("/api/oracle/users"),
            json={
                "name": "IntTest_Create",
                "birthday": "1990-05-15",
                "mother_name": "Sarah",
                "country": "US",
                "city": "New York",
            },
        )
        assert (
            resp.status_code == 201
        ), f"Expected 201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["name"] == "IntTest_Create"
        assert data["mother_name"] == "Sarah"
        assert data["id"] > 0
        assert "created_at" in data

    def test_list_users(self, api_client):
        """GET /api/oracle/users returns user list."""
        # Create a user first
        api_client.post(
            api_url("/api/oracle/users"),
            json={
                "name": "IntTest_List",
                "birthday": "1985-03-20",
                "mother_name": "Jane",
            },
        )
        resp = api_client.get(api_url("/api/oracle/users"))
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_get_user(self, api_client):
        """GET /api/oracle/users/{id} returns a specific user."""
        # Create user
        create_resp = api_client.post(
            api_url("/api/oracle/users"),
            json={
                "name": "IntTest_Get",
                "birthday": "1988-07-04",
                "mother_name": "Emma",
            },
        )
        user_id = create_resp.json()["id"]

        resp = api_client.get(api_url(f"/api/oracle/users/{user_id}"))
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == user_id
        assert data["name"] == "IntTest_Get"
        assert data["mother_name"] == "Emma"

    def test_update_user(self, api_client):
        """PUT /api/oracle/users/{id} updates and returns the user."""
        # Create user
        create_resp = api_client.post(
            api_url("/api/oracle/users"),
            json={
                "name": "IntTest_Update",
                "birthday": "1992-11-30",
                "mother_name": "Linda",
            },
        )
        user_id = create_resp.json()["id"]

        # Update
        resp = api_client.put(
            api_url(f"/api/oracle/users/{user_id}"),
            json={"city": "London"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["city"] == "London"

    def test_delete_user(self, api_client):
        """DELETE /api/oracle/users/{id} soft-deletes the user."""
        # Create user
        create_resp = api_client.post(
            api_url("/api/oracle/users"),
            json={
                "name": "IntTest_Delete",
                "birthday": "1995-01-01",
                "mother_name": "Mary",
            },
        )
        user_id = create_resp.json()["id"]

        # Delete
        resp = api_client.delete(api_url(f"/api/oracle/users/{user_id}"))
        assert resp.status_code == 200

        # Verify gone from list
        list_resp = api_client.get(api_url("/api/oracle/users?search=IntTest_Delete"))
        users = list_resp.json().get("users", [])
        user_ids = [u["id"] for u in users]
        assert user_id not in user_ids

    def test_create_duplicate_user_409(self, api_client):
        """Creating a user with same name+birthday should return 409."""
        payload = {
            "name": "IntTest_Dupe",
            "birthday": "1990-01-01",
            "mother_name": "Dupe",
        }
        api_client.post(api_url("/api/oracle/users"), json=payload)
        resp = api_client.post(api_url("/api/oracle/users"), json=payload)
        assert resp.status_code == 409

    def test_get_nonexistent_user_404(self, api_client):
        """Getting a nonexistent user should return 404."""
        resp = api_client.get(api_url("/api/oracle/users/999999"))
        assert resp.status_code == 404


@pytest.mark.api
class TestOracleReadings:
    """Test Oracle reading computation endpoints."""

    def test_create_reading(self, api_client):
        """POST /api/oracle/reading returns FC60 + numerology data."""
        resp = api_client.post(
            api_url("/api/oracle/reading"),
            json={"datetime": "2024-06-15T14:30:00+00:00"},
        )
        assert (
            resp.status_code == 200
        ), f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "fc60" in data
        assert "numerology" in data
        assert "zodiac" in data
        assert "summary" in data
        # FC60 should have element, polarity etc.
        assert "element" in data["fc60"]
        assert "polarity" in data["fc60"]

    def test_question_sign(self, api_client):
        """POST /api/oracle/question returns answer with sign number."""
        resp = api_client.post(
            api_url("/api/oracle/question"),
            json={"question": "Will the integration tests pass?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert data["answer"] in ("yes", "no", "maybe")
        assert "sign_number" in data
        assert isinstance(data["sign_number"], int)

    def test_name_reading(self, api_client):
        """POST /api/oracle/name returns destiny number."""
        resp = api_client.post(
            api_url("/api/oracle/name"),
            json={"name": "Integration Test"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "destiny_number" in data
        assert "soul_urge" in data
        assert "letters" in data
        assert len(data["letters"]) > 0

    def test_daily_insight(self, api_client):
        """GET /api/oracle/daily returns date and insight."""
        resp = api_client.get(api_url("/api/oracle/daily"))
        assert resp.status_code == 200
        data = resp.json()
        assert "date" in data
        assert "insight" in data

    def test_reading_history(self, api_client):
        """GET /api/oracle/readings returns stored readings."""
        # Create a reading first
        api_client.post(
            api_url("/api/oracle/reading"),
            json={"datetime": "2024-01-01T00:00:00+00:00"},
        )
        resp = api_client.get(api_url("/api/oracle/readings"))
        assert resp.status_code == 200
        data = resp.json()
        assert "readings" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_get_single_reading(self, api_client):
        """GET /api/oracle/readings/{id} returns a specific reading."""
        # Create a reading
        create_resp = api_client.post(
            api_url("/api/oracle/reading"),
            json={"datetime": "2024-03-15T10:00:00+00:00"},
        )
        # Get readings list to find the ID
        list_resp = api_client.get(api_url("/api/oracle/readings?limit=1"))
        readings = list_resp.json().get("readings", [])
        if readings:
            reading_id = readings[0]["id"]
            resp = api_client.get(api_url(f"/api/oracle/readings/{reading_id}"))
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == reading_id


@pytest.mark.api
class TestOracleAudit:
    """Test Oracle audit log endpoint."""

    def test_audit_log(self, api_client):
        """GET /api/oracle/audit returns audit entries."""
        # Create a user to generate audit entries
        api_client.post(
            api_url("/api/oracle/users"),
            json={
                "name": "IntTest_Audit",
                "birthday": "1990-01-01",
                "mother_name": "AuditMom",
            },
        )
        resp = api_client.get(api_url("/api/oracle/audit"))
        assert resp.status_code == 200
        data = resp.json()
        assert "entries" in data
        assert "total" in data
        # Should have at least the user.create entry
        assert data["total"] >= 1


@pytest.mark.api
class TestEncryptionRoundtrip:
    """Verify encryption at rest for sensitive fields."""

    def test_mother_name_encrypted_in_db(self, api_client, db_connection):
        """After creating a user via API, DB should have ENC4: prefix on mother_name."""
        resp = api_client.post(
            api_url("/api/oracle/users"),
            json={
                "name": "IntTest_Encrypt",
                "birthday": "1990-06-15",
                "mother_name": "EncryptedMom",
            },
        )
        assert resp.status_code == 201
        user_id = resp.json()["id"]

        # Query DB directly
        result = db_connection.execute(
            text("SELECT mother_name FROM oracle_users WHERE id = :id"),
            {"id": user_id},
        )
        row = result.fetchone()
        assert row is not None
        db_value = row[0]
        # Should be encrypted (ENC4: prefix) if encryption is configured
        # If encryption key is set, value should start with ENC4:
        # If not configured, it will be plaintext
        import os

        if os.environ.get("NPS_ENCRYPTION_KEY"):
            assert db_value.startswith(
                "ENC4:"
            ), f"Expected ENC4: prefix, got: {db_value[:20]}..."

    def test_api_returns_plaintext(self, api_client):
        """API GET should return decrypted (plaintext) mother_name."""
        # Create user
        create_resp = api_client.post(
            api_url("/api/oracle/users"),
            json={
                "name": "IntTest_Decrypt",
                "birthday": "1985-12-25",
                "mother_name": "PlaintextMom",
            },
        )
        user_id = create_resp.json()["id"]

        # Read back via API
        resp = api_client.get(api_url(f"/api/oracle/users/{user_id}"))
        assert resp.status_code == 200
        data = resp.json()
        assert data["mother_name"] == "PlaintextMom"


@pytest.mark.api
class TestAuthLegacyFallback:
    """Test that legacy API_SECRET_KEY auth works."""

    def test_unauthenticated_returns_401(self):
        """Requests without auth should get 401."""
        import requests

        resp = requests.get(api_url("/api/oracle/users"), timeout=5)
        assert resp.status_code == 401

    def test_wrong_token_returns_403(self):
        """Requests with wrong token should get 403."""
        import requests

        resp = requests.get(
            api_url("/api/oracle/users"),
            headers={"Authorization": "Bearer wrong-token"},
            timeout=5,
        )
        assert resp.status_code == 403

    def test_legacy_api_key_works(self, api_client):
        """Legacy Bearer <API_SECRET_KEY> should grant admin access."""
        resp = api_client.get(api_url("/api/oracle/users"))
        assert resp.status_code == 200


@pytest.mark.api
class TestSoftDeleteVerification:
    """Verify soft-delete works correctly through API layer."""

    def test_deleted_user_not_in_list(self, api_client):
        """After DELETE, user should not appear in GET /users."""
        # Create user
        create_resp = api_client.post(
            api_url("/api/oracle/users"),
            json={
                "name": "IntTest_SoftDelAPI",
                "birthday": "1990-06-15",
                "mother_name": "SoftDelMom",
            },
        )
        assert create_resp.status_code == 201
        user_id = create_resp.json()["id"]

        # Delete
        del_resp = api_client.delete(api_url(f"/api/oracle/users/{user_id}"))
        assert del_resp.status_code == 200

        # Verify not in list
        list_resp = api_client.get(
            api_url("/api/oracle/users?search=IntTest_SoftDelAPI")
        )
        users = list_resp.json().get("users", [])
        assert all(u["id"] != user_id for u in users)

        # Verify GET by ID returns 404
        get_resp = api_client.get(api_url(f"/api/oracle/users/{user_id}"))
        assert get_resp.status_code == 404

    def test_deleted_user_cannot_be_updated(self, api_client):
        """After DELETE, PUT should return 404."""
        create_resp = api_client.post(
            api_url("/api/oracle/users"),
            json={
                "name": "IntTest_SoftDelUpd",
                "birthday": "1990-06-15",
                "mother_name": "SoftDelMom",
            },
        )
        user_id = create_resp.json()["id"]
        api_client.delete(api_url(f"/api/oracle/users/{user_id}"))

        # Try to update deleted user
        resp = api_client.put(
            api_url(f"/api/oracle/users/{user_id}"),
            json={"city": "Ghost City"},
        )
        assert resp.status_code == 404

    def test_can_recreate_after_soft_delete(self, api_client):
        """After soft-delete, creating user with same name+birthday should succeed."""
        payload = {
            "name": "IntTest_SoftDelRecreate",
            "birthday": "1990-06-15",
            "mother_name": "RecreateMom",
        }
        # Create and delete
        create_resp = api_client.post(api_url("/api/oracle/users"), json=payload)
        user_id = create_resp.json()["id"]
        api_client.delete(api_url(f"/api/oracle/users/{user_id}"))

        # Recreate with same name+birthday should work (soft-deleted != active)
        recreate_resp = api_client.post(api_url("/api/oracle/users"), json=payload)
        assert recreate_resp.status_code == 201
        assert recreate_resp.json()["id"] != user_id
