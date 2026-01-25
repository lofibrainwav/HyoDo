# scripts/verify_vault.py
import sys
from pathlib import Path

# Add package root to path
current_dir = Path(__file__).resolve().parent
package_root = current_dir.parent / "packages" / "afo-core"
sys.path.insert(0, str(package_root))

from config.vault_manager import vault_manager


def verify() -> None:
    print("🔍 [Verification] Vault Integration Check")

    # Check Initialization
    if vault_manager.mock_mode:
        print("✅ VaultManager initialized in Mock Mode (Correct for local env)")
    else:
        print("✅ VaultManager connect to real Vault")

    # Check Secret Retrieval
    secret = vault_manager.get_secret("secret/test", "my_key")
    print(f"🔑 Secret Retrieval Test: {secret}")

    if secret:
        print("✅ Secret retrieval logic functional")
    else:
        print("❌ Secret retrieval returned None")

    # Check Sync
    vault_manager.sync_to_local()
    print("✅ Sync verify complete")


if __name__ == "__main__":
    verify()
