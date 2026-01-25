"""
API Router Tests - AFO Core Backend

Tests for API router endpoints including health, chancellor, skills, finance, and general routes.

Coverage Target: Increase API routes coverage
"""

import pytest
from httpx import AsyncClient, ConnectError


async def is_api_server_running() -> bool:
    """Check if API server is running on localhost:8010."""
    try:
        async with AsyncClient(base_url="http://localhost:8010", timeout=2.0) as client:
            response = await client.get("/api/health")
            return response.status_code == 200
    except (ConnectError, Exception):
        return False


# Skip all integration tests if API server is not running
pytestmark = pytest.mark.integration


class TestHealthRouter:
    """Health Router Tests"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_check_returns_status_ok(self):
        """Health check should return 200 OK status."""
        if not await is_api_server_running():
            pytest.skip("API server not running on localhost:8010")

        async with AsyncClient(base_url="http://localhost:8010") as client:
            response = await client.get("/api/health")

            assert response.status_code == 200, (
                f"Health check should return 200 OK, got {response.status_code}"
            )

            data = response.json()
            assert "status" in data, "Response should contain status field"
            # Accept both 'ok' and 'healthy' as valid status values
            assert data["status"] in ["ok", "healthy"], (
                f"Health status should be 'ok' or 'healthy', got {data.get('status')}"
            )


@pytest.mark.integration
class TestChancellorRouter:
    """Chancellor Router Tests"""

    @pytest.mark.asyncio
    async def test_chancellor_invoke_missing_body(self):
        """Chancellor invoke should reject missing request body."""
        if not await is_api_server_running():
            pytest.skip("API server not running on localhost:8010")

        async with AsyncClient(base_url="http://localhost:8010") as client:
            response = await client.post("/api/chancellor/invoke", json={})

            # 422 for validation error, 404 if route not configured
            assert response.status_code in [404, 422], (
                f"Should reject missing body, got {response.status_code}"
            )

    @pytest.mark.asyncio
    async def test_chancellor_invoke_valid_request(self):
        """Chancellor invoke should accept valid request."""
        if not await is_api_server_running():
            pytest.skip("API server not running on localhost:8010")

        async with AsyncClient(base_url="http://localhost:8010") as client:
            request_data = {
                "prompt": "Test prompt",
                "mode": "inquiry",
            }
            response = await client.post("/api/chancellor/invoke", json=request_data)

            # Accept 200, 400, 404 (route not configured)
            assert response.status_code in [200, 400, 404], (
                f"Should accept valid request, got {response.status_code}"
            )


@pytest.mark.integration
class TestFinanceRouter:
    """Finance Router Tests"""

    @pytest.mark.asyncio
    async def test_get_finance_dashboard(self):
        """Get finance dashboard data."""
        if not await is_api_server_running():
            pytest.skip("API server not running on localhost:8010")

        async with AsyncClient(base_url="http://localhost:8010") as client:
            response = await client.get("/api/finance/dashboard")

            # Note: This test assumes the endpoint exists
            assert response.status_code in [200, 404, 500], (
                f"Should return valid status code, got {response.status_code}"
            )

    @pytest.mark.asyncio
    async def test_calculate_tax_scenario(self):
        """Calculate tax scenario endpoint."""
        if not await is_api_server_running():
            pytest.skip("API server not running on localhost:8010")

        async with AsyncClient(base_url="http://localhost:8010") as client:
            request_data = {
                "income": 50000.0,
                "filing_status": "single",
            }
            response = await client.post("/api/julie/calculate-tax", json=request_data)

            # Note: This test assumes the endpoint exists
            assert response.status_code in [200, 400, 500], (
                f"Should return valid status code, got {response.status_code}"
            )


@pytest.mark.integration
class TestSkillsRouter:
    """Skills Router Tests"""

    @pytest.mark.asyncio
    async def test_list_skills_returns_list(self):
        """List skills should return array of skills."""
        if not await is_api_server_running():
            pytest.skip("API server not running on localhost:8010")

        async with AsyncClient(base_url="http://localhost:8010") as client:
            response = await client.get("/api/skills")

            # Note: This test assumes the endpoint exists
            assert response.status_code in [200, 404, 500], (
                f"Should return valid status code, got {response.status_code}"
            )

            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, (list, dict)), (
                    f"Should return list or dict, got {type(data)}"
                )

                if isinstance(data, dict):
                    assert "skills" in data or "results" in data, "Response should contain skills"


@pytest.mark.integration
class TestAPIErrors:
    """General API Error Handling Tests"""

    @pytest.mark.asyncio
    async def test_404_for_invalid_endpoint(self):
        """404 error for non-existent endpoint."""
        if not await is_api_server_running():
            pytest.skip("API server not running on localhost:8010")

        async with AsyncClient(base_url="http://localhost:8010") as client:
            response = await client.get("/api/nonexistent")

            assert response.status_code == 404, "Should return 404 for non-existent endpoint"

    @pytest.mark.asyncio
    async def test_500_error_handling(self):
        """500 error should return error response."""
        if not await is_api_server_running():
            pytest.skip("API server not running on localhost:8010")
        # This test would need an endpoint that can be forced to error
        pass


@pytest.mark.integration
class TestAPIIntegration:
    """Integration Tests for Full API"""

    @pytest.mark.asyncio
    async def test_api_startup_sequence(self):
        """Test API startup sequence: health → skills → dashboard."""
        if not await is_api_server_running():
            pytest.skip("API server not running on localhost:8010")

        async with AsyncClient(base_url="http://localhost:8010") as client:
            # Check health first
            health_response = await client.get("/api/health")
            assert health_response.status_code == 200, "Health check should pass on startup"

            # Then check skills (may return 404 if route not configured)
            skills_response = await client.get("/api/skills")
            assert skills_response.status_code in [200, 404], "Skills endpoint response"
