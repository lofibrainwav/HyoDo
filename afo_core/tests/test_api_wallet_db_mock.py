# Trinity Score: 90.0 (Established by Chancellor)
# TICKET-104 Phase 2: DB Support implemented
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from AFO.api_wallet import APIWallet


@pytest.fixture
def mock_db_conn() -> None:
    """Create mock database connection with cursor context manager"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # Support context manager for cursor
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value.__exit__.return_value = None

    # Handle connection pool behavior (getconn returns connection)
    mock_conn.getconn.return_value = mock_conn

    return mock_conn, mock_cursor


def test_db_initialization_with_conn(mock_db_conn) -> None:
    """Test wallet initializes with DB connection"""
    conn, _ = mock_db_conn

    wallet = APIWallet(db_connection=conn, use_vault=False)

    assert wallet.use_db is True
    assert wallet.db is conn
    assert conn.cursor.called


def test_add_to_database(mock_db_conn) -> None:
    """Test adding key to database"""
    conn, cursor = mock_db_conn
    cursor.fetchone.return_value = [123]

    wallet = APIWallet(db_connection=conn, use_vault=False)
    wallet.cipher = MagicMock()
    wallet.cipher.encrypt.return_value = b"enc"

    key_id = wallet.add("test_db_key", "sk-key")

    assert key_id == 123
    cursor.execute.assert_called()
    assert "INSERT INTO api_keys" in cursor.execute.call_args[0][0]


def test_get_from_database(mock_db_conn) -> None:
    """Test retrieving key from database"""
    conn, cursor = mock_db_conn
    cursor.fetchone.return_value = {
        "id": 1,
        "name": "k",
        "encrypted_key": "enc_k",
        "key_type": "api",
        "read_only": False,
        "service": "open",
        "description": "",
        "key_hash": "h",
        "created_at": datetime(2023, 1, 1),
        "last_accessed": None,
        "access_count": 0,
    }

    wallet = APIWallet(db_connection=conn, use_vault=False)
    wallet.cipher = MagicMock()
    wallet.cipher.decrypt.return_value = b"decrypted_key"

    k = wallet.get("k")
    assert k == "decrypted_key"


def test_list_from_database(mock_db_conn) -> None:
    """Test listing keys from database"""
    conn, cursor = mock_db_conn
    cursor.fetchall.return_value = [
        {
            "name": "k1",
            "service": "s1",
            "key_type": "api",
            "read_only": False,
            "description": "",
            "created_at": None,
            "encrypted_key": "e1",
            "last_accessed": None,
        },
        {
            "name": "k2",
            "service": "s2",
            "key_type": "api",
            "read_only": True,
            "description": "",
            "created_at": None,
            "encrypted_key": "e2",
            "last_accessed": None,
        },
    ]

    wallet = APIWallet(db_connection=conn, use_vault=False)
    keys = wallet.list_keys()

    assert len(keys) == 2
    assert keys[0]["name"] == "k1"


def test_delete_from_database(mock_db_conn) -> None:
    """Test deleting key from database"""
    conn, cursor = mock_db_conn
    cursor.rowcount = 1

    wallet = APIWallet(db_connection=conn, use_vault=False)
    assert wallet.delete("k") is True
    assert "DELETE FROM" in cursor.execute.call_args[0][0]


def test_update_access_stats_db(mock_db_conn) -> None:
    """Test updating access stats in database"""
    conn, cursor = mock_db_conn
    cursor.fetchone.return_value = {"encrypted_key": "openai"}

    wallet = APIWallet(db_connection=conn, use_vault=False)
    wallet.cipher = MagicMock()
    wallet.cipher.decrypt.return_value = b"key"

    with patch.dict(
        sys.modules,
        {"redis": MagicMock(), "AFO.utils.redis_connection": MagicMock()},
    ):
        # Trigger access stats update via get
        wallet.get("k")

    # Verify UPDATE was called
    update_calls = [
        call for call in cursor.execute.call_args_list if "UPDATE api_keys" in str(call)
    ]
    assert len(update_calls) > 0


def test_db_transaction_rollback(mock_db_conn) -> None:
    """Test transaction rollback on error"""
    conn, cursor = mock_db_conn

    # Create wallet first (before setting side_effect)
    wallet = APIWallet(db_connection=conn, use_vault=False)
    wallet.cipher = MagicMock()
    wallet.cipher.encrypt.return_value = b"e"

    # Now set side_effect for add operation
    cursor.execute.side_effect = Exception("DB Fail")

    with pytest.raises(Exception):
        wallet.add("fail", "k")

    conn.rollback.assert_called()
