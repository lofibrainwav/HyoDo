# Trinity Score: 97.0 (Phase 33 Audit Module Refactoring)
"""
AFO Audit Trail Module - Backward Compatibility Wrapper

This file serves as a backward compatibility wrapper for the refactored
audit package. All functionality has been moved to the audit/ directory for
better organization and maintainability.

Original: 926 lines → Refactored: 5 files, 150-250 lines each
- audit/models.py - Pydantic models and enums (200 lines)
- audit/storage.py - Storage backends (300 lines)
- audit/trail.py - Main AuditTrail class (250 lines)
- audit/middleware.py - FastAPI integration (100 lines)
- audit/__init__.py - Package exports (50 lines)

Migration completed: 2026-01-16
Phase 33: Large file refactoring for better maintainability
"""

# Backward compatibility - import from refactored package
from .audit import (
    AuditEvent,
    AuditEventType,
    AuditQuery,
    AuditSeverity,
    AuditStats,
    AuditStorage,
    AuditTrail,
    FileAuditStorage,
    audit_middleware,
    get_audit_trail,
    set_audit_trail,
    setup_audit,
)

# Re-export for backward compatibility (keeping original interface)
__all__ = [
    # Enums
    "AuditEventType",
    "AuditSeverity",
    # Models
    "AuditEvent",
    "AuditQuery",
    "AuditStats",
    # Storage
    "AuditStorage",
    "FileAuditStorage",
    # Main Class
    "AuditTrail",
    # Global Functions
    "get_audit_trail",
    "set_audit_trail",
    # FastAPI Integration
    "audit_middleware",
    "setup_audit",
]
