# Trinity Score: 90.0 (Established by Chancellor)
"""Test API Health Check
Tests the core health check functionality for system monitoring.
"""

import pytest
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    """Test that health endpoint returns 200 OK"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()


def test_system_health_endpoint(client: TestClient) -> None:
    """Test system health endpoint with metrics"""
    response = client.get("/api/system/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data


def test_health_response_structure(client: TestClient) -> None:
    """Test health response has required fields"""
    response = client.get("/health")
    data = response.json()

    required_fields = ["status", "timestamp", "service"]
    for field in required_fields:
        assert field in data

    assert data["status"] in ["balanced", "warning", "imbalanced", "unbalanced"]
