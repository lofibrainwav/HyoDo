# Trinity Score: 97.0 (Phase 30 Complete Refactoring)
"""
Browser Auth MCP Integration - Backward Compatibility Wrapper

This file now serves as a backward compatibility wrapper for the refactored
browser_auth package. All functionality has been moved to the browser_auth/
directory for better organization and maintainability.

Original: 592 lines → Refactored: 4 files, 150-200 lines each
- browser_auth/mcp_tools.py - MCPBrowserTools 클래스
- browser_auth/mcp_auth.py - MCPIntegratedAuth 클래스
- browser_auth/mcp_utils.py - 헬퍼 함수들
- browser_auth/__init__.py - 패키지 초기화

Migration completed: 2026-01-16
"""

# Backward compatibility - import from refactored package
from browser_auth import MCPBrowserTools, MCPIntegratedAuth, mcp_auth_experiment

# Re-export for backward compatibility
__all__ = ["MCPBrowserTools", "MCPIntegratedAuth", "mcp_auth_experiment"]
