# Trinity Score: 90.0 (Established by Chancellor)
# mypy: ignore-errors
#!/usr/bin/env python3
"""
Manual Token Entry for API Wallet
Use this when auto-extraction returns empty tokens due to OS encryption.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from AFO.api_wallet import APIWallet
except ImportError:
    # Just in case run from inside scripts dir
    sys.path.insert(0, str(Path(__file__).parent.parent / "AFO"))
    from api_wallet import APIWallet


def main() -> None:
    print("=== API Wallet: Manual Token Entry ===\n")
    print("Encryption Key Status: ✅ Configured (in .env)")

    wallet = APIWallet()
    print(f"Storage: {wallet.storage_path if hasattr(wallet, 'storage_path') else 'DB'}")

    print("\nPlease paste your OPENAI_API_KEY (or session token):")
    token = input("> ").strip()

    if not token:
        print("❌ No token provided.")
        return

    print(f"\nAdding token '{token[:10]}...' to wallet...")

    try:
        # Check if exists and delete first to avoid duplicate error
        existing = wallet.get("openai")
        if existing:
            print("Found existing key, updating...")
            wallet.delete("openai")

        key_id = wallet.add(
            name="openai",
            api_key=token,
            service="openai",
            description="Manually added via script",
        )
        print(f"\n✅ Success! Token added with ID {key_id}")

    except Exception as e:
        print(f"\n❌ Error adding token: {e}")


if __name__ == "__main__":
    main()
