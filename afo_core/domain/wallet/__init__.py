# Trinity Score: 95.0 (Established by Chancellor)
"""
AFO Domain Wallet Package (domain/wallet/__init__.py)

Strangler Fig Facade for the API Wallet system.
TICKET-103: Added VAULT_AVAILABLE, VaultKMS, PSYCOPG2_AVAILABLE, CRYPTO_AVAILABLE exports.
"""

from .core import APIWallet
from .crypto import CRYPTO_AVAILABLE, PSYCOPG2_AVAILABLE, Fernet, MockFernet, get_cipher
from .kms import VAULT_AVAILABLE, VaultKMS
from .models import KeyMetadata, WalletSummary

__all__ = [
    # Models
    "KeyMetadata",
    "WalletSummary",
    # Crypto
    "Fernet",
    "MockFernet",
    "get_cipher",
    "CRYPTO_AVAILABLE",
    "PSYCOPG2_AVAILABLE",
    # KMS
    "VaultKMS",
    "VAULT_AVAILABLE",
    # Core
    "APIWallet",
]
