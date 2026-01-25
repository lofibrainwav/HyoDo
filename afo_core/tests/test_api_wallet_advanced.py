# Trinity Score: 90.0 (Established by Chancellor)
import importlib
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from AFO.api_wallet import APIWallet

# Load wallet-specific fixtures
pytest_plugins = ["tests.conftest_wallet"]


# 1. Vault KMS Integration Tests
def test_wallet_has_vault_attributes() -> None:
    """Test that APIWallet exposes use_vault and encryption_key attributes (TICKET-104)."""
    wallet = APIWallet()

    # Verify attributes exist
    assert hasattr(wallet, "use_vault")
    assert hasattr(wallet, "encryption_key")

    # Default behavior: use_vault should be False when VAULT_ENABLED is not set
    assert wallet.use_vault is False

    # encryption_key should be set (either from settings or auto-generated)
    assert wallet.encryption_key is not None
    assert len(wallet.encryption_key) > 0


@pytest.mark.skip(
    reason="Vault mock requires complex module patching - tested via integration tests"
)
def test_wallet_init_vault_success_mocked() -> None:
    """Placeholder for mocked Vault test - requires integration testing."""
    pass


def test_wallet_init_vault_failure_fallback() -> None:
    """Test that wallet falls back gracefully when Vault is unavailable."""
    # When VAULT_ENABLED is not set or Vault is unavailable,
    # use_vault should be False and encryption_key should still be set
    wallet = APIWallet(use_vault=True)

    # Without proper Vault setup, it should fall back
    assert wallet.use_vault is False
    assert wallet.encryption_key is not None
    assert len(wallet.encryption_key) > 0


# 3. Cryptography Missing (MockFernet)
@pytest.mark.skip(reason="Module reload test unstable - MockFernet tested in test_api_wallet.py")
def test_mock_fernet_fallback() -> None:
    # Force reload api_wallet with CRYPTO_AVAILABLE=False logic
    # We cheat by importing, then mocking the global variable if it was already True,
    # OR we use the reload technique.
    # Since we are in the same process, reloading is safer.

    # Use local KMS mode to avoid vault fail-closed policy
    with patch.dict(os.environ, {"API_WALLET_KMS": "local"}):
        with patch.dict(sys.modules):
            # Remove it so we can re-import
            if "AFO.api_wallet" in sys.modules:
                del sys.modules["AFO.api_wallet"]
            if "api_wallet" in sys.modules:
                del sys.modules["api_wallet"]

            # We also need to ensure Fernet doesn't import properly or we force disable it
            # The code checks: try: from cryptography.fernet import Fernet ... except ImportError: ...

            # Let's force ImportError for cryptography
            sys.modules["cryptography"] = None  # type: ignore[assignment]
            sys.modules["cryptography.fernet"] = None  # type: ignore[assignment]

            # Now import
            # Use import_module to ensure it loads freshly and registers in sys.modules
            api_wallet = importlib.import_module("AFO.api_wallet")

            assert api_wallet.CRYPTO_AVAILABLE is False
            assert api_wallet.Fernet.__name__ == "MockFernet"

            # Now test the MockFernet class logic
            wallet = api_wallet.APIWallet(encryption_key="x" * 44)
            enc = wallet.cipher.encrypt(b"test")
            # MockFernet returns base64 string of data
            # Wait, the MockFernet implementation in api_wallet.py:
            # return base64.urlsafe_b64encode(data)
            import base64

            expected = base64.urlsafe_b64encode(b"test")
            assert enc == expected

            dec = wallet.cipher.decrypt(enc)
            assert dec == b"test"


# 3. CLI Tests using main()
@pytest.mark.skip(
    reason="CLI interface changed after modularization. See test_api_wallet_cli.py for current tests."
)
def test_cli_execution() -> None:
    from AFO.api_wallet import main

    # Mock create_wallet to return a mock wallet
    mock_wallet_instance = MagicMock()
    mock_wallet_instance.add.return_value = 1
    mock_wallet_instance.get.return_value = "API_KEY"
    mock_wallet_instance.list_keys.return_value = [{"name": "test", "service": "test"}]
    mock_wallet_instance.delete.return_value = True

    # We must patch create_wallet in the exact module main() looks for it.
    # main() is in AFO.api_wallet, and it calls create_wallet() from global scope of AFO.api_wallet.
    # So patching AFO.api_wallet.create_wallet is correct.

    with patch("AFO.api_wallet.create_wallet", return_value=mock_wallet_instance):
        # Test ADD
        with patch.object(
            sys, "argv", ["api_wallet.py", "add", "test_key", "secret_val", "openai"]
        ):
            main()
            mock_wallet_instance.add.assert_called_with("test_key", "secret_val", service="openai")

        # Test GET
        with patch.object(sys, "argv", ["api_wallet.py", "get", "test_key"]):
            main()
            mock_wallet_instance.get.assert_called_with("test_key")

        # Test LIST
        with patch.object(sys, "argv", ["api_wallet.py", "list"]):
            main()
            mock_wallet_instance.list_keys.assert_called()

        # Test DELETE
        with patch.object(sys, "argv", ["api_wallet.py", "delete", "test_key"]):
            main()
            mock_wallet_instance.delete.assert_called_with("test_key")


# 4. DB Method Tests (Directly calling them to ensure SQL construction works)
# TICKET-104 Phase 2: Updated to match current implementation
def test_db_methods_sql_construction() -> None:
    """Test DB methods SQL construction with mocked connection"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # Setup cursor context manager (MagicMock has getconn by default, so it uses that path)
    mock_conn.getconn.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value.__exit__.return_value = None

    wallet = APIWallet(db_connection=mock_conn, use_vault=False)

    # Verify use_db is True
    assert wallet.use_db is True

    # Test _ensure_db_table was called during init
    assert mock_cursor.execute.called
    # Check CREATE TABLE was in one of the calls
    create_table_calls = [
        call for call in mock_cursor.execute.call_args_list if "CREATE TABLE" in str(call)
    ]
    assert len(create_table_calls) > 0

    # Reset mock for add test
    mock_cursor.reset_mock()
    mock_cursor.fetchone.return_value = [10]
    wallet.cipher = MagicMock()
    wallet.cipher.encrypt.return_value = b"encrypted"

    # Test _add_to_db via add()
    key_id = wallet.add("test_name", "test_key", key_type="api", service="openai")
    assert key_id == 10

    # Verify INSERT was called
    insert_calls = [
        call for call in mock_cursor.execute.call_args_list if "INSERT INTO api_keys" in str(call)
    ]
    assert len(insert_calls) > 0
