# Trinity Score: 90.0 (Established by Chancellor)
"""
AFO API Wallet Compatibility Layer (AFO/api_wallet.py)

This module provides backward compatibility for code that imports from AFO.api_wallet.
The actual implementation is in domain/wallet/. We import directly to avoid
`api_wallet` module resolution loops when running AFO/api_server.py.
"""

from domain.wallet import (
    CRYPTO_AVAILABLE,
    PSYCOPG2_AVAILABLE,
    VAULT_AVAILABLE,
    APIWallet,
    Fernet,
    KeyMetadata,
    MockFernet,
    VaultKMS,
    WalletSummary,
    get_cipher,
)


def create_wallet(
    encryption_key: str | None = None,
    db_connection: object | None = None,
    use_vault: bool | None = None,
) -> APIWallet:
    """Factory function to create a new APIWallet instance."""
    return APIWallet(
        encryption_key=encryption_key,
        db_connection=db_connection,
        use_vault=use_vault,
    )


# Global singleton instance
wallet = create_wallet()


def main() -> None:
    """CLI entry point for API Wallet management."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="API Wallet CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new API key")
    add_parser.add_argument("name", help="Key name")
    add_parser.add_argument("value", help="Key value")
    add_parser.add_argument("--service", default="", help="Service name")

    # Get command
    get_parser = subparsers.add_parser("get", help="Get an API key")
    get_parser.add_argument("name", help="Key name")

    # List command
    subparsers.add_parser("list", help="List all keys")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a key")
    delete_parser.add_argument("name", help="Key name")

    args = parser.parse_args()

    if args.command == "add":
        try:
            wallet.add(args.name, args.value, service=args.service)
            print(f"Key '{args.name}' added successfully")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.command == "get":
        result = wallet.get(args.name)
        if result:
            print(result)
        else:
            print(f"Key '{args.name}' not found", file=sys.stderr)
            sys.exit(1)
    elif args.command == "list":
        keys = wallet.list_keys()
        for key in keys:
            print(f"{key.get('name', 'unknown')}: created {key.get('created_at', 'unknown')}")
    elif args.command == "delete":
        try:
            wallet.delete(args.name)
            print(f"Key '{args.name}' deleted")
        except KeyError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


__all__ = [
    "APIWallet",
    "create_wallet",
    "main",
    "wallet",
    "KeyMetadata",
    "WalletSummary",
    "Fernet",
    "MockFernet",
    "get_cipher",
    "CRYPTO_AVAILABLE",
    "PSYCOPG2_AVAILABLE",
    "VaultKMS",
    "VAULT_AVAILABLE",
]
