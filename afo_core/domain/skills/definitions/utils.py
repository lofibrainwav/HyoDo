import os
from typing import cast

from AFO.config.settings import get_settings


def get_mcp_server_url() -> str | None:
    """Helper to get MCP server URL from environment"""
    try:
        settings = get_settings()
        return cast(
            "str | None",
            getattr(settings, "MCP_SERVER_URL", os.getenv("MCP_SERVER_URL")),
        )
    except Exception:  # nosec
        return os.getenv("MCP_SERVER_URL")
