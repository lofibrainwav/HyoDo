# Trinity Score: 90.0 (Established by Chancellor)
"""
Input Server Tests

Tests for AFO Input Server - env text parsing and health endpoint.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from AFO.input_server import app, parse_env_text

client = TestClient(app)

# Mocks for skipped tests (defined to avoid Pyright errors)
mock_storage = MagicMock()
mock_wallet_module = MagicMock()


# 1. Unit Tests for Logic
def test_parse_env_text() -> None:
    text = """
    OPENAI_API_KEY=sk-1234
    ANTHROPIC_API_KEY: sk-ant-5678
    "GITHUB_TOKEN": "ghp_abcd"
    N8N_URL "https://n8n.com"
    # Comment line
    INVALID_LINE
    """
    parsed = parse_env_text(text)

    assert len(parsed) == 4
    # Check key mappings
    assert parsed[0] == ("OPENAI_API_KEY", "sk-1234", "openai")
    assert parsed[1] == ("ANTHROPIC_API_KEY", "sk-ant-5678", "anthropic")
    assert parsed[2] == ("GITHUB_TOKEN", "ghp_abcd", "github")
    assert parsed[3] == ("N8N_URL", "https://n8n.com", "n8n")


def test_parse_env_text_quotes() -> None:
    text = """KEY_A="value_a"\nKEY_B='value_b'"""
    parsed = parse_env_text(text)
    assert parsed[0][1] == "value_a"
    assert parsed[1][1] == "value_b"


# 2. API Endpoints
def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "AFO Input Server",
        "organ": "胃 (Stomach)",
    }


@pytest.mark.skip(reason="Home page endpoint not yet implemented in new input_server.py")
@patch("httpx.AsyncClient.get")
def test_home_page_no_keys(mock_get) -> None:
    mock_get.return_value = MagicMock(status_code=500)
    response = client.get("/")
    assert response.status_code == 200
    assert "AFO Input Server" in response.text
    assert "text/html" in response.headers["content-type"]


@pytest.mark.skip(reason="Home page endpoint not yet implemented in new input_server.py")
@patch("httpx.AsyncClient.get")
def test_home_page_with_keys(mock_get) -> None:
    mock_response = MagicMock(status_code=200)
    mock_response.json.return_value = {
        "keys": [
            {
                "name": "test_key",
                "provider": "openai",
                "created_at": "2024-01-01T00:00:00",
            }
        ]
    }
    mock_get.return_value = mock_response

    response = client.get("/")
    assert response.status_code == 200
    assert "test_key" in response.text
    assert "openai" in response.text


@pytest.mark.skip(reason="/add_key endpoint not implemented in minimal input_server.py")
@patch("httpx.AsyncClient.post")
def test_add_key_success(mock_post) -> None:
    mock_post.return_value = MagicMock(status_code=200)

    # Ensure save_input_to_db is mockable via sys.modules or direct attribute
    # Since we mocked input_storage at top, AFO.input_server.save_input_to_db is a Mock

    response = client.post(
        "/add_key",
        data={
            "name": "new_key",
            "provider": "openai",
            "key": "sk-test-key",
            "description": "test key",
        },
    )
    assert response.status_code == 200
    # Capture print output or verify db call
    assert mock_storage.save_input_to_db.called


@pytest.mark.skip(reason="/add_key endpoint not implemented in minimal input_server.py")
@patch("httpx.AsyncClient.post")
def test_add_key_wallet_failure(mock_post) -> None:
    mock_post.return_value = MagicMock(status_code=400, json=lambda: {"detail": "Bad Request"})

    response = client.post(
        "/add_key", data={"name": "fail_key", "provider": "openai", "key": "sk-fail"}
    )
    assert response.status_code == 200


def test_api_status() -> None:
    # Note: INPUT_STORAGE_AVAILABLE was removed during input_server refactoring
    # Skip this test unconditionally since the variable no longer exists
    pytest.skip("INPUT_STORAGE_AVAILABLE removed after input_server refactoring - test obsolete")


# 3. Bulk Import Logic
@pytest.mark.skip(reason="/bulk_import endpoint not implemented in minimal input_server.py")
def test_bulk_import_direct_wallet() -> None:
    # Mock APIWallet class
    mock_wallet_instance = MagicMock()
    mock_wallet_module.APIWallet.return_value = mock_wallet_instance

    # Setup get to return None then something (simulate not exists then exists)
    mock_wallet_instance.get.side_effect = [None, "exists"]

    input_text = "NEW_KEY=sk-new\nEXISTING_KEY=sk-old"

    response = client.post("/bulk_import", data={"bulk_text": input_text})

    assert response.status_code == 200
    assert mock_wallet_instance.add.call_count == 1  # Only one added


@pytest.mark.skip(reason="/bulk_import endpoint not implemented in minimal input_server.py")
def test_bulk_import_empty_handling() -> None:
    # If empty text passed (but valid param), it should handle it gracefully or invalid
    response = client.post("/bulk_import", data={"bulk_text": " "})  # Space is not empty param
    assert response.status_code == 200  # Redirects with error "파싱된 환경 변수가 없습니다"


def test_get_history() -> None:
    # Note: INPUT_STORAGE_AVAILABLE was removed during input_server refactoring
    # Skip this test unconditionally since the variable no longer exists
    pytest.skip("INPUT_STORAGE_AVAILABLE removed after input_server refactoring - test obsolete")


def test_get_history_unavailable() -> None:
    # Note: INPUT_STORAGE_AVAILABLE was removed during input_server refactoring
    # Skip this test unconditionally since the variable no longer exists
    pytest.skip("INPUT_STORAGE_AVAILABLE removed after input_server refactoring - test obsolete")


# ============================================================================
# 4. JSON API Endpoint Tests (New RESTful endpoints)
# ============================================================================
@patch("input_server.api.httpx.AsyncClient")
def test_api_add_key_success(mock_async_client: MagicMock) -> None:
    """Test /api/add_key JSON endpoint with successful response."""
    # Setup mock async client
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success"}

    mock_client_instance = MagicMock()

    async def mock_post(*args, **kwargs):
        return mock_response

    mock_client_instance.post = mock_post
    mock_client_instance.__aenter__ = lambda s: mock_client_instance
    mock_client_instance.__aexit__ = lambda s, *args: None

    # Make the mock return proper async context manager
    mock_async_client.return_value.__aenter__ = lambda self: mock_client_instance
    mock_async_client.return_value.__aexit__ = lambda self, *args: None

    response = client.post(
        "/api/add_key",
        json={
            "name": "test_api_key",
            "provider": "openai",
            "key": "sk-test-12345",
            "description": "Test API key",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["name"] == "test_api_key"
    assert data["provider"] == "openai"


@patch("input_server.api.httpx.AsyncClient")
def test_api_add_key_wallet_error(mock_async_client: MagicMock) -> None:
    """Test /api/add_key JSON endpoint with API Wallet error."""
    # Setup mock async client to return error
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"detail": "Key already exists"}

    mock_client_instance = MagicMock()

    async def mock_post(*args, **kwargs):
        return mock_response

    mock_client_instance.post = mock_post
    mock_client_instance.__aenter__ = lambda s: mock_client_instance
    mock_client_instance.__aexit__ = lambda s, *args: None

    mock_async_client.return_value.__aenter__ = lambda self: mock_client_instance
    mock_async_client.return_value.__aexit__ = lambda self, *args: None

    response = client.post(
        "/api/add_key",
        json={
            "name": "existing_key",
            "provider": "anthropic",
            "key": "sk-ant-12345",
        },
    )

    assert response.status_code == 400
    assert "API Wallet error" in response.json()["detail"]


def test_api_add_key_validation_error() -> None:
    """Test /api/add_key JSON endpoint with missing required fields."""
    # Missing 'key' field
    response = client.post(
        "/api/add_key",
        json={
            "name": "incomplete_key",
            "provider": "openai",
        },
    )

    assert response.status_code == 422  # Validation error


@patch("input_server.api.is_api_wallet_available")
@patch("input_server.api.import_single_key")
def test_api_bulk_import_success(
    mock_import_key: MagicMock, mock_wallet_available: MagicMock
) -> None:
    """Test /api/bulk_import JSON endpoint with successful imports."""
    # Setup mocks
    mock_wallet_available.return_value = True
    mock_import_key.return_value = "success"

    response = client.post(
        "/api/bulk_import",
        json={
            "bulk_text": "OPENAI_API_KEY=sk-test-123\nANTHROPIC_API_KEY=sk-ant-456"
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["counts"]["success"] == 2
    assert data["counts"]["failed"] == 0


@patch("input_server.api.is_api_wallet_available")
@patch("input_server.api.import_single_key")
def test_api_bulk_import_partial(
    mock_import_key: MagicMock, mock_wallet_available: MagicMock
) -> None:
    """Test /api/bulk_import JSON endpoint with partial success."""
    mock_wallet_available.return_value = True
    # First succeeds, second fails
    mock_import_key.side_effect = ["success", "Connection error"]

    response = client.post(
        "/api/bulk_import",
        json={
            "bulk_text": "KEY_ONE=value1\nKEY_TWO=value2"
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "partial"
    assert data["counts"]["success"] == 1
    assert data["counts"]["failed"] == 1
    assert len(data["failed_keys"]) == 1


def test_api_bulk_import_empty_text() -> None:
    """Test /api/bulk_import JSON endpoint with empty/invalid text."""
    response = client.post(
        "/api/bulk_import",
        json={
            "bulk_text": "   \n# Only comments\n   "
        },
    )

    assert response.status_code == 400
    assert "No valid environment variables" in response.json()["detail"]


def test_api_bulk_import_validation_error() -> None:
    """Test /api/bulk_import JSON endpoint with missing bulk_text."""
    response = client.post(
        "/api/bulk_import",
        json={},
    )

    assert response.status_code == 422  # Validation error
