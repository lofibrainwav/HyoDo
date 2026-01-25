# Trinity Score: 90.0 (Established by Chancellor)
# mypy: ignore-errors
"""Conftest for API Wallet tests.
Ensures proper module isolation between tests that manipulate sys.modules.
"""

import sys

import pytest

# Store original module state
_original_modules = {}


@pytest.fixture(autouse=True)
def isolate_api_wallet_module() -> None:
    """Autouse fixture that cleans up api_wallet module state before and after each test.
    This prevents test pollution when tests reload the module with different configurations.
    """
    # Store modules we might need to restore
    modules_to_track = [
        "AFO.api_wallet",
        "api_wallet",
        "AFO.kms.vault_kms",
        "kms.vault_kms",
        "cryptography",
        "cryptography.fernet",
        "psycopg2",
    ]

    saved_modules = {}
    for mod in modules_to_track:
        if mod in sys.modules:
            saved_modules[mod] = sys.modules[mod]

    yield  # Run the test

    # Restore original module state after test
    for mod in modules_to_track:
        if mod in saved_modules:
            sys.modules[mod] = saved_modules[mod]
        elif mod in sys.modules:
            # Remove modules that were added during test
            del sys.modules[mod]
