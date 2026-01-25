from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

# Trinity Score: 90.0 (Established by Chancellor)
"""AFO Antigravity Module (眞善美孝永)

Stub module for core Antigravity functionality to unblock Gate.
Full implementation in api_server.py.
"""


logger = logging.getLogger(__name__)


@dataclass
class Antigravity:
    """Core Antigravity configuration singleton."""

    ENVIRONMENT: str = field(default_factory=lambda: os.getenv("AFO_ENV", "production"))
    VERSION: str = "1.0.0"
    DEBUG: bool = field(default_factory=lambda: os.getenv("AFO_DEBUG", "false").lower() == "true")
    DRY_RUN: bool = field(
        default_factory=lambda: os.getenv("AFO_DRY_RUN", "false").lower() == "true"
    )
    AUTO_DEPLOY: bool = field(
        default_factory=lambda: os.getenv("AFO_AUTO_DEPLOY", "true").lower() == "true"
    )
    DRY_RUN_DEFAULT: bool = field(
        default_factory=lambda: os.getenv("AFO_DRY_RUN_DEFAULT", "true").lower() == "true"
    )

    def get_version(self) -> str:
        """Get AFO version."""
        return self.VERSION

    def get_config(self) -> dict[str, Any]:
        """Get configuration dict."""
        return {
            "version": self.VERSION,
            "environment": self.ENVIRONMENT,
            "debug": self.DEBUG,
        }


# Singleton instance
antigravity = Antigravity()

# Environment setting (backwards compatibility)
ENVIRONMENT = antigravity.ENVIRONMENT
VERSION = antigravity.VERSION


def get_version() -> str:
    """Get AFO version."""
    return VERSION


def get_config() -> dict[str, Any]:
    """Get configuration stub."""
    return antigravity.get_config()


__all__ = [
    "Antigravity",
    "antigravity",
    "ENVIRONMENT",
    "VERSION",
    "get_version",
    "get_config",
]
