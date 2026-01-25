# Trinity Score: 90.0 (Established by Chancellor)
import os
import sys
from unittest.mock import MagicMock, patch

# We need to control 'hvac' import availability
from AFO.kms.vault_kms import VaultKMS


def test_init_no_hvac() -> None:
    # Simulate hvac missing
    with patch.dict(sys.modules, {"hvac": None}):
        # Need to reload module or patch the 'hvac' symbol in the module if already imported
        with patch("AFO.kms.vault_kms.hvac", None):
            kms = VaultKMS()
            assert kms.client is None
            assert kms.is_available() is False


def test_init_success() -> None:
    mock_hvac_module = MagicMock()
    mock_client = MagicMock()
    mock_hvac_module.Client.return_value = mock_client

    # Patch the 'hvac' attribute in the imported module to be our mock
    with (
        patch("AFO.kms.vault_kms.hvac", mock_hvac_module),
        patch.dict(os.environ, {"VAULT_ADDR": "http://test", "VAULT_TOKEN": "token"}),
    ):
        kms = VaultKMS()
        assert kms.client is mock_client


def test_is_available_success() -> None:
    kms = VaultKMS()
    kms.client = MagicMock()
    kms.client.is_authenticated.return_value = True
    assert kms.is_available() is True


def test_is_available_failure() -> None:
    kms = VaultKMS()
    kms.client = MagicMock()
    kms.client.is_authenticated.side_effect = Exception("Auth fail")
    assert kms.is_available() is False


def test_get_encryption_key_success() -> None:
    kms = VaultKMS()
    kms.client = MagicMock()
    kms.client.is_authenticated.return_value = True

    # Mock kv.v2.read_secret_version
    mock_secrets = MagicMock()
    kms.client.secrets = mock_secrets
    mock_secrets.kv.v2.read_secret_version.return_value = {
        "data": {"data": {"encryption_key": "secret_key"}}
    }

    assert kms.get_encryption_key() == "secret_key"


def test_get_encryption_key_unavailable() -> None:
    kms = VaultKMS()
    # No client
    assert kms.get_encryption_key() is None


def test_get_encryption_key_error() -> None:
    kms = VaultKMS()
    kms.client = MagicMock()
    kms.client.is_authenticated.return_value = True
    kms.client.secrets.kv.v2.read_secret_version.side_effect = Exception("Read fail")

    assert kms.get_encryption_key() is None


def test_set_encryption_key_success() -> None:
    kms = VaultKMS()
    kms.client = MagicMock()
    kms.client.is_authenticated.return_value = True

    assert kms.set_encryption_key("new_key") is True
    kms.client.secrets.kv.v2.create_or_update_secret.assert_called_once()


def test_set_encryption_key_error() -> None:
    kms = VaultKMS()
    kms.client = MagicMock()
    kms.client.is_authenticated.return_value = True
    kms.client.secrets.kv.v2.create_or_update_secret.side_effect = Exception("Write fail")

    assert kms.set_encryption_key("new_key") is False
