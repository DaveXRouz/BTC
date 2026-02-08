"""Phase 4.4: Frontend-API integration tests — CORS, schema compatibility, docs."""

import pytest
import requests

from conftest import api_url


@pytest.mark.frontend
class TestCORS:
    """Verify CORS configuration allows frontend origin."""

    def test_cors_allows_localhost_5173(self):
        """API should allow requests from http://localhost:5173."""
        resp = requests.options(
            api_url("/api/health"),
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization,Content-Type",
            },
            timeout=5,
        )
        assert resp.status_code == 200
        assert "http://localhost:5173" in resp.headers.get(
            "access-control-allow-origin", ""
        )

    def test_cors_allows_localhost_3000(self):
        """API should allow requests from http://localhost:3000."""
        resp = requests.options(
            api_url("/api/health"),
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
            timeout=5,
        )
        assert resp.status_code == 200
        assert "http://localhost:3000" in resp.headers.get(
            "access-control-allow-origin", ""
        )


@pytest.mark.frontend
class TestSchemaCompatibility:
    """Verify API response shapes match frontend TypeScript types."""

    def test_oracle_users_list_schema(self, api_client):
        """GET /api/oracle/users returns paginated response matching OracleUserListResponse."""
        resp = api_client.get(api_url("/api/oracle/users"))
        assert resp.status_code == 200
        data = resp.json()
        # Must have pagination fields
        assert "users" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["users"], list)

    def test_oracle_user_shape(self, api_client):
        """User objects should match frontend OracleUser interface."""
        # Create a user
        create_resp = api_client.post(
            api_url("/api/oracle/users"),
            json={
                "name": "IntTest_Shape",
                "birthday": "1990-01-01",
                "mother_name": "ShapeMom",
                "name_persian": "test",
                "country": "US",
                "city": "NYC",
            },
        )
        assert create_resp.status_code == 201
        user = create_resp.json()

        # Check all fields the frontend expects
        expected_fields = [
            "id",
            "name",
            "name_persian",
            "birthday",
            "mother_name",
            "mother_name_persian",
            "country",
            "city",
            "created_at",
            "updated_at",
        ]
        for field in expected_fields:
            assert field in user, f"Missing field '{field}' in user response"

    def test_reading_response_shape(self, api_client):
        """Reading response should match frontend OracleReading interface."""
        resp = api_client.post(
            api_url("/api/oracle/reading"),
            json={"datetime": "2024-06-15T14:30:00+00:00"},
        )
        assert resp.status_code == 200
        data = resp.json()

        # FC60 shape
        fc60 = data.get("fc60", {})
        fc60_fields = [
            "cycle",
            "element",
            "polarity",
            "stem",
            "branch",
            "year_number",
            "month_number",
            "day_number",
            "energy_level",
            "element_balance",
        ]
        for field in fc60_fields:
            assert field in fc60, f"Missing FC60 field '{field}'"

        # Numerology shape
        num = data.get("numerology", {})
        num_fields = [
            "life_path",
            "day_vibration",
            "personal_year",
            "personal_month",
            "personal_day",
            "interpretation",
        ]
        for field in num_fields:
            assert field in num, f"Missing numerology field '{field}'"

    def test_health_ready_shape(self, api_client):
        """Health ready response should match frontend HealthStatus interface."""
        resp = api_client.get(api_url("/api/health/ready"))
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert data["status"] in ("healthy", "degraded", "unhealthy")
        assert "checks" in data
        assert isinstance(data["checks"], dict)


@pytest.mark.frontend
class TestSwaggerUI:
    """Verify API docs are accessible."""

    def test_openapi_json(self):
        """GET /openapi.json should return the OpenAPI schema."""
        resp = requests.get(api_url("/openapi.json"), timeout=5)
        assert resp.status_code == 200
        data = resp.json()
        assert "openapi" in data
        assert "paths" in data

    def test_swagger_docs(self):
        """GET /docs should return Swagger UI HTML."""
        resp = requests.get(api_url("/docs"), timeout=5)
        assert resp.status_code == 200
        assert "swagger" in resp.text.lower() or "openapi" in resp.text.lower()
