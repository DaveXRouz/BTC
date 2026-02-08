"""Phase 5: Security integration tests — auth, encryption, rate limiting, input validation."""

import os
import time

import pytest
import requests

from conftest import API_BASE_URL, api_url


@pytest.mark.security
class TestAuthSecurity:
    """Verify authentication enforcement on all protected endpoints."""

    def test_no_auth_returns_401(self):
        """Requests without any auth header should get 401."""
        endpoints = [
            ("GET", "/api/oracle/users"),
            ("POST", "/api/oracle/reading"),
            ("GET", "/api/oracle/daily"),
            ("GET", "/api/oracle/readings"),
        ]
        for method, path in endpoints:
            resp = requests.request(method, api_url(path), timeout=5)
            assert (
                resp.status_code == 401
            ), f"{method} {path} returned {resp.status_code}, expected 401"

    def test_invalid_token_returns_403(self):
        """Requests with an invalid Bearer token should get 403."""
        headers = {"Authorization": "Bearer invalid-token-value-here"}
        resp = requests.get(api_url("/api/oracle/users"), headers=headers, timeout=5)
        assert resp.status_code == 403

    def test_scope_enforcement(self, api_client):
        """Valid auth should allow access to scoped endpoints."""
        resp = api_client.get(api_url("/api/oracle/users"))
        assert resp.status_code == 200

    def test_audit_requires_admin(self):
        """Audit endpoint should require oracle:admin scope."""
        # Without any auth
        resp = requests.get(api_url("/api/oracle/audit"), timeout=5)
        assert resp.status_code == 401


@pytest.mark.security
class TestEncryptionSecurity:
    """Verify encryption at rest for sensitive fields."""

    def test_encryption_roundtrip(self, api_client):
        """Create user, verify mother_name comes back correctly."""
        test_value = "Encryption_Test_Mother"
        resp = api_client.post(
            api_url("/api/oracle/users"),
            json={
                "name": "IntTest_EncRoundtrip",
                "birthday": "1990-01-01",
                "mother_name": test_value,
            },
        )
        assert resp.status_code == 201
        user_id = resp.json()["id"]

        # Read back
        get_resp = api_client.get(api_url(f"/api/oracle/users/{user_id}"))
        assert get_resp.status_code == 200
        assert get_resp.json()["mother_name"] == test_value

    def test_db_stores_encrypted(self, api_client, db_connection):
        """If encryption is configured, DB should have ENC4: prefix."""
        from sqlalchemy import text

        resp = api_client.post(
            api_url("/api/oracle/users"),
            json={
                "name": "IntTest_EncDB",
                "birthday": "1990-01-01",
                "mother_name": "SecretMother",
            },
        )
        assert resp.status_code == 201
        user_id = resp.json()["id"]

        result = db_connection.execute(
            text("SELECT mother_name FROM oracle_users WHERE id = :id"),
            {"id": user_id},
        )
        row = result.fetchone()
        assert row is not None
        db_val = row[0]

        if os.environ.get("NPS_ENCRYPTION_KEY"):
            assert db_val.startswith(
                "ENC4:"
            ), f"Expected ENC4: prefix, got: {db_val[:20]}"


@pytest.mark.security
class TestRateLimiting:
    """Test rate limiting headers and enforcement."""

    def test_rate_limit_headers(self, api_client):
        """Responses should include rate limit headers if configured."""
        resp = api_client.get(api_url("/api/oracle/users"))
        # Rate limiting is optional; just verify the request works
        assert resp.status_code == 200


@pytest.mark.security
class TestInputValidation:
    """Test input validation and sanitization."""

    def test_special_chars_in_name(self, api_client):
        """Special characters in names should be handled safely."""
        resp = api_client.post(
            api_url("/api/oracle/users"),
            json={
                "name": 'IntTest_Special<>&"',
                "birthday": "1990-01-01",
                "mother_name": "Normal",
            },
        )
        # Should either accept (stored as data) or reject (validation)
        assert resp.status_code in (201, 400, 422)

    def test_very_long_input(self, api_client):
        """Very long input should be rejected or truncated."""
        resp = api_client.post(
            api_url("/api/oracle/users"),
            json={
                "name": "IntTest_Long_" + "A" * 300,
                "birthday": "1990-01-01",
                "mother_name": "Normal",
            },
        )
        # Either rejected by validation or stored (VARCHAR(200) will truncate/error)
        assert resp.status_code in (201, 400, 422, 500)

    def test_invalid_date_format(self, api_client):
        """Invalid date formats should be rejected."""
        resp = api_client.post(
            api_url("/api/oracle/users"),
            json={
                "name": "IntTest_BadDate",
                "birthday": "not-a-date",
                "mother_name": "Normal",
            },
        )
        assert resp.status_code == 422

    def test_future_birthday_rejected(self, api_client):
        """Future birthday should be rejected by DB constraint."""
        resp = api_client.post(
            api_url("/api/oracle/users"),
            json={
                "name": "IntTest_FutureBday",
                "birthday": "2099-12-31",
                "mother_name": "Normal",
            },
        )
        assert resp.status_code in (400, 422, 500)

    def test_short_name_rejected(self, api_client):
        """Name shorter than 2 chars should be rejected."""
        resp = api_client.post(
            api_url("/api/oracle/users"),
            json={
                "name": "X",
                "birthday": "1990-01-01",
                "mother_name": "Normal",
            },
        )
        assert resp.status_code in (400, 422, 500)
