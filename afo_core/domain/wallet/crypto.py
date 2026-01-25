from __future__ import annotations

import base64
import logging
import os
from typing import Any

from cryptography.fernet import Fernet

# Trinity Score: 95.0 (Established by Chancellor)
"""
AFO Wallet Crypto (domain/wallet/crypto.py)

Encryption utilities for API Wallet.
TICKET-103: Added PSYCOPG2_AVAILABLE for database support detection.
"""


logger = logging.getLogger(__name__)

# Try to import cryptography, fallback to mock mode
try:
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# Try to import psycopg2 for PostgreSQL support (TICKET-103)
try:
    import psycopg2  # noqa: F401

    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


class MockFernet:
    """Mock Fernet for development without cryptography package"""

    def __init__(self, key: bytes) -> None:
        self.key = key

    def encrypt(self, data: bytes) -> bytes:
        return b"MOCK_" + data

    def decrypt(self, data: bytes) -> bytes:
        if data.startswith(b"MOCK_"):
            return data[5:]
        return data

    @staticmethod
    def generate_key() -> bytes:
        return base64.urlsafe_b64encode(os.urandom(32))


if not CRYPTO_AVAILABLE:
    Fernet = MockFernet  # type: ignore


def get_cipher(key: str | bytes) -> Any:
    """Get Fernet cipher instance"""
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)
