"""Phase 3.1: API health endpoint integration tests."""

import pytest

from conftest import api_url


@pytest.mark.api
class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_check(self, api_client):
        """GET /api/health returns 200 with status healthy."""
        resp = api_client.get(api_url("/api/health"))
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["version"] == "4.0.0"

    def test_readiness_check(self, api_client):
        """GET /api/health/ready returns 200 with real connection checks."""
        resp = api_client.get(api_url("/api/health/ready"))
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "checks" in data
        checks = data["checks"]
        # Database should be healthy if Postgres is running
        assert checks.get("database") == "healthy"
        # Scanner is not deployed
        assert checks.get("scanner_service") == "not_deployed"
        # Oracle uses direct mode (V3 imports)
        assert checks.get("oracle_service") == "direct_mode"

    def test_health_no_auth_required(self):
        """Health endpoints should work without authentication."""
        import requests

        resp = requests.get(api_url("/api/health"), timeout=5)
        assert resp.status_code == 200

    def test_readiness_no_auth_required(self):
        """Readiness endpoint should work without authentication."""
        import requests

        resp = requests.get(api_url("/api/health/ready"), timeout=5)
        assert resp.status_code == 200
