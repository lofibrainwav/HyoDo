# Trinity Score: 98.0 (Phase 33 Audit Module Package)
"""AFO Audit Trail Module - Refactored Package"""

from .middleware import audit_middleware, setup_audit
from .models import AuditEvent, AuditEventType, AuditQuery, AuditSeverity, AuditStats
from .storage import AuditStorage, FileAuditStorage
from .trail import AuditTrail, get_audit_trail, set_audit_trail

__all__ = [
    # Models
    "AuditEvent",
    "AuditEventType",
    "AuditSeverity",
    "AuditQuery",
    "AuditStats",
    # Storage
    "AuditStorage",
    "FileAuditStorage",
    # Trail Manager
    "AuditTrail",
    "get_audit_trail",
    "set_audit_trail",
    # FastAPI Integration
    "audit_middleware",
    "setup_audit",
]
