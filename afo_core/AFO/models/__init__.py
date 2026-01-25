# AFO Models Package
"""Central model exports for AFO Kingdom.

Re-exports wallet models for backward compatibility.
"""

API_PROVIDERS = ["openai", "anthropic", "google", "azure", "aws", "ollama"]

# Re-export wallet models for backward compatibility
try:
    from api.routes.wallet.models import (
        WalletAPIKeyRequest,
        WalletAPIResponse,
        WalletSessionRequest,
        WalletStatusResponse,
    )
except ImportError:
    # Fallback for when wallet models aren't available
    WalletAPIKeyRequest = None  # type: ignore
    WalletStatusResponse = None  # type: ignore
    WalletSessionRequest = None  # type: ignore
    WalletAPIResponse = None  # type: ignore

__all__ = [
    "API_PROVIDERS",
    "WalletAPIKeyRequest",
    "WalletStatusResponse",
    "WalletSessionRequest",
    "WalletAPIResponse",
]
