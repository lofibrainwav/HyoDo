from __future__ import annotations

import logging

# Trinity Score: 92.0 (Established by Chancellor)
"""
AFO Wallet KMS (domain/wallet/kms.py)

HashiCorp Vault KMS integration for API Wallet.
TICKET-103: Modularization - moved from kms/vault_kms.py
"""

logger = logging.getLogger(__name__)

# Try to import hvac for Vault support
try:
    import hvac

    VAULT_AVAILABLE = True
    del hvac  # Imported for availability check only
except ImportError:
    VAULT_AVAILABLE = False


# Re-export VaultKMS from the original location for backwards compatibility
try:
    from AFO.kms.vault_kms import VaultKMS
except ImportError:
    # Fallback: Define a stub VaultKMS if import fails
    class VaultKMS:  # type: ignore[no-redef]
        """Stub VaultKMS when hvac is not available."""

        def __init__(self) -> None:
            self.client = None

        def is_available(self) -> bool:
            return False

        def get_encryption_key(self) -> str | None:
            return None

        def set_encryption_key(self, key: str) -> bool:
            _ = key  # Unused in stub
            return False


__all__ = ["VaultKMS", "VAULT_AVAILABLE"]
