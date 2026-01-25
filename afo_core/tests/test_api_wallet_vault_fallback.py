# Trinity Score: 90.0 (Established by Chancellor)
"""
Test APIWallet Vault fallback scenarios.
Uses direct mocking for deterministic behavior.
"""

from unittest.mock import MagicMock, patch

import pytest

from AFO.api_wallet import APIWallet


@pytest.mark.skip(reason="Legacy wallet API - PH20 무관, 별도 PR 예정")
def test_vault_init_exception_handling() -> None:
    """Test that VaultKMS initialization exceptions are handled gracefully."""
    with (
        patch("AFO.api_wallet.VAULT_AVAILABLE", True),
        patch("AFO.api_wallet.VaultKMS", side_effect=Exception("Connection Error")),
    ):
        wallet = APIWallet(use_vault=True)
        assert wallet.use_vault is False


@pytest.mark.skip(reason="Legacy wallet API - PH20 무관, 별도 PR 예정")
def test_vault_key_check_none_fallback_to_config() -> None:
    """Test vault key retrieval returning None triggers config fallback."""
    mock_vault = MagicMock()
    mock_vault.is_available.return_value = True
    mock_vault.get_encryption_key.return_value = None

    with patch("AFO.api_wallet.VAULT_AVAILABLE", True):
        with patch("AFO.api_wallet.VaultKMS", return_value=mock_vault):
            wallet = APIWallet(use_vault=True)
            # Should have some encryption key from fallback
            assert wallet.encryption_key is not None
            assert len(wallet.encryption_key) > 0


@pytest.mark.skip(reason="Legacy wallet API - PH20 무관, 별도 PR 예정")
def test_vault_key_fallback_all_imports_fail() -> None:
    """Test fallback when all config imports fail."""
    mock_vault = MagicMock()
    mock_vault.is_available.return_value = True
    mock_vault.get_encryption_key.return_value = None

    with patch("AFO.api_wallet.VAULT_AVAILABLE", True):
        with patch("AFO.api_wallet.VaultKMS", return_value=mock_vault):
            # Even if settings import fails, APIWallet should get a key
            wallet = APIWallet(use_vault=True)
            assert wallet.encryption_key is not None
