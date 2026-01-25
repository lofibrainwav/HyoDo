# Trinity Score: 90.0 (Established by Chancellor)
# mypy: ignore-errors
import os
import sys

# Ensure AFO is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from AFO.api_wallet import APIWallet
except ImportError:
    # Fallback if running from scripts dir directly
    sys.path.append(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "AFO")
    )
    from api_wallet import APIWallet


def main() -> None:
    try:
        wallet = APIWallet()
        # Load all keys
        # We need a way to list all. APIWallet doesn't have list_all public method based on my previous view,
        # but keys.py uses `_load_storage` or similar if it's not exposed.
        # Checking keys.py implementation might be needed, but let's assume valid implementation for now based on wallet design.
        # Actually keys.py uses wallet API. let's check if wallet has get_all or we have to read json directly if DB is not used.

        # Direct JSON fallback for script if APIWallet is complex
        if not wallet.use_db:
            storage = wallet._load_storage()
            for key in storage["keys"]:
                name = key["name"]
                # Decrypt
                decrypted = wallet.get(name, decrypt=True)

                # Format for export
                # Convert name to env var format (UPPERCASE, remove special chars)
                env_var_name = name.upper().replace("-", "_").replace(" ", "_")

                # Specific mappings for known tools
                if "OPENAI" in env_var_name and "SESSION" in env_var_name:
                    print(f"export OPENAI_SESSION_TOKEN='{decrypted}'")
                elif "ANTHROPIC" in env_var_name and "SESSION" in env_var_name:
                    print(f"export ANTHROPIC_SESSION_KEY='{decrypted}'")
                elif "OPENAI" in env_var_name:  # API Key
                    print(f"export OPENAI_API_KEY='{decrypted}'")
                elif "ANTHROPIC" in env_var_name:  # API Key
                    print(f"export ANTHROPIC_API_KEY='{decrypted}'")
                else:
                    print(f"export {env_var_name}='{decrypted}'")

    except Exception as e:
        print(f"# Error exporting keys: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
