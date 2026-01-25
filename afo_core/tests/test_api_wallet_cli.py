# Trinity Score: 90.0 (Established by Chancellor)
"""
API Wallet CLI Tests

Tests CLI interface for API Wallet management.
"""

from unittest.mock import MagicMock, patch

import pytest

# Import from root-level module directly for proper mock patching
from api_wallet import main as cli


def test_cli_add_key() -> None:
    with patch("sys.argv", ["api_wallet.py", "add", "test_key", "sk-123"]):
        mock_wallet = MagicMock()
        mock_wallet.add.return_value = 1

        with patch("api_wallet.wallet", mock_wallet):
            cli()
            mock_wallet.add.assert_called_with("test_key", "sk-123", service="")


def test_cli_add_key_failure() -> None:
    with patch("sys.argv", ["api_wallet.py", "add", "test_key", "sk-123"]):
        mock_wallet = MagicMock()
        mock_wallet.add.side_effect = ValueError("Duplicate")

        with patch("api_wallet.wallet", mock_wallet):
            with pytest.raises(SystemExit):
                cli()


def test_cli_get_key() -> None:
    with patch("sys.argv", ["api_wallet.py", "get", "test_key"]):
        mock_wallet = MagicMock()
        mock_wallet.get.return_value = "decrypted_sk"

        with patch("api_wallet.wallet", mock_wallet):
            cli()
            mock_wallet.get.assert_called_with("test_key")


def test_cli_list_keys() -> None:
    with patch("sys.argv", ["api_wallet.py", "list"]):
        mock_wallet = MagicMock()
        mock_wallet.list_keys.return_value = [{"name": "k1", "created_at": "now"}]

        with patch("api_wallet.wallet", mock_wallet):
            cli()
            mock_wallet.list_keys.assert_called()


def test_cli_delete_key() -> None:
    with patch("sys.argv", ["api_wallet.py", "delete", "test_key"]):
        mock_wallet = MagicMock()
        mock_wallet.delete.return_value = True

        with patch("api_wallet.wallet", mock_wallet):
            cli()
            mock_wallet.delete.assert_called_with("test_key")


def test_cli_no_args() -> None:
    with patch("sys.argv", ["api_wallet.py"]):
        with pytest.raises(SystemExit) as e:
            cli()
        assert e.value.code == 1
