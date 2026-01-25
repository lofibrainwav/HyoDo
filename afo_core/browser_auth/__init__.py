# Trinity Score: 95.0 (Phase 30 Browser Auth Package)
"""Browser Authentication Module - MCP Integration Package"""

from .mcp_auth import MCPIntegratedAuth
from .mcp_tools import MCPBrowserTools
from .mcp_utils import mcp_auth_experiment

# Backward compatibility - expose main classes and functions
__all__ = [
    "MCPBrowserTools",
    "MCPIntegratedAuth",
    "mcp_auth_experiment",
    # Additional exports for comprehensive testing
    "MCPIntegration",  # Alias for backward compatibility
]
