# Trinity Score: 92.0 (Phase 30 Utils Refactoring)
"""Input Server Utilities - Environment Variable Parsing and Helpers"""

import re
from typing import Any

import httpx

# Environment variable parsing patterns
ENV_PATTERNS = [
    (r"^([A-Z_][A-Z0-9_]*)\s*=\s*(.+)$", "key_value"),
    (r"^([A-Z_][A-Z0-9_]*)\s*:\s*(.+)$", "key_colon"),
    (r'"([A-Z_][A-Z0-9_]*)":\s*"([^"]+)"', "json"),
    (r'^([A-Z_][A-Z0-9_]*)\s+"([^"]+)"$', "key_quoted"),
]

# Service mapping for API keys
SERVICE_MAPPING = {
    "OPENAI_API_KEY": "openai",
    "ANTHROPIC_API_KEY": "anthropic",
    "N8N_URL": "n8n",
    "API_YUNGDEOK": "n8n",
    "N8N_API_TOKEN": "n8n",
    "REDIS_URL": "redis",
    "POSTGRES_PASSWORD": "postgres",
    "DISCORD_BOT_TOKEN": "discord",
    "CLOUDFLARE_API_TOKEN": "cloudflare",
    "GITHUB_TOKEN": "github",
}


def parse_env_text(text: str) -> list[tuple[str, str, str]]:
    """Parse environment variables from text input.

    Supports multiple formats:
    - KEY=VALUE
    - KEY: VALUE
    - "KEY": "VALUE"
    - KEY "VALUE"

    Returns:
        List of tuples (key, value, service)
    """
    parsed = []
    lines = text.split("\n")

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        for pattern, _ in ENV_PATTERNS:
            match = re.match(pattern, line)
            if match:
                key, value = match.groups()
                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]
                service = SERVICE_MAPPING.get(key, "other")
                parsed.append((key, value.strip(), service))
                break

    return parsed


async def is_api_wallet_available(url: str) -> bool:
    """Check if API Wallet server is available."""
    async with httpx.AsyncClient(timeout=2.0) as client:
        try:
            resp = await client.get(f"{url}/health")
            return bool(resp.status_code == 200)
        except Exception:
            return False


async def import_single_key(
    name: str, value: str, service: str, wallet: Any, api_server_url: str | None
) -> str:
    """Import a single API key (Success, Skipped, or Error message).

    Args:
        name: API key name
        value: API key value
        service: Service name (openai, anthropic, etc.)
        wallet: APIWallet instance (optional)
        api_server_url: API Wallet server URL (optional)

    Returns:
        "success", "skipped", or error message
    """
    # 1. Try direct API Wallet storage
    if wallet:
        try:
            if wallet.get(name, decrypt=False):
                return "skipped"
            wallet.add(
                name=name,
                api_key=value,
                key_type="api",
                read_only=True,
                service=service,
                description=f"Bulk import: {name}",
            )
            return "success"
        except Exception as e:
            if "already exists" in str(e).lower():
                return "skipped"
            return str(e)

    # 2. Try API Wallet server storage (fallback)
    if api_server_url:
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                # Check if key already exists
                chk = await client.get(f"{api_server_url}/api/wallet/get/{name}", timeout=2.0)
                if chk.status_code == 200:
                    return "skipped"

                # Add the key
                resp = await client.post(
                    f"{api_server_url}/api/wallet/add",
                    json={
                        "name": name,
                        "api_key": value,
                        "key_type": "api",
                        "read_only": True,
                        "service": service,
                        "description": f"Bulk import: {name}",
                    },
                )
                if resp.status_code == 200:
                    return "success"

                # Handle error response
                err_detail = resp.json().get("detail", "Unknown error")
                return "skipped" if "already exists" in err_detail.lower() else err_detail
            except Exception as e:
                return str(e)

    return "API Wallet unavailable"
