# Trinity Score: 94.0 (Phase 33 Audit Module Refactoring)
"""Main Audit Trail Manager and Convenience Functions"""

from __future__ import annotations

import hashlib
import logging
from typing import TYPE_CHECKING, Any

from .models import AuditEvent, AuditEventType, AuditQuery, AuditSeverity, AuditStats
from .storage import AuditStorage, FileAuditStorage

if TYPE_CHECKING:
    from fastapi import Request, Response

logger = logging.getLogger(__name__)


# ============================================================================
# Main Audit Trail Manager (美 - Elegant Interface)
# ============================================================================


class AuditTrail:
    """Main Audit Trail manager (美 - Elegant Interface)

    Provides a unified interface for audit logging across the AFO Kingdom.
    Supports multiple storage backends and async operations.

    Usage:
        audit = AuditTrail()
        await audit.log(
            event_type=AuditEventType.DATA_CREATE,
            action="Created new user account",
            resource="users",
            user_id="user-123",
        )
    """

    _instance: AuditTrail | None = None

    def __init__(self, storage: AuditStorage | None = None) -> None:
        self._storage = storage or FileAuditStorage()
        self._enabled = True

    @classmethod
    def get_instance(cls) -> AuditTrail:
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = AuditTrail()
        return cls._instance

    @classmethod
    def set_instance(cls, instance: AuditTrail) -> None:
        """Set singleton instance (for testing)"""
        cls._instance = instance

    async def log(
        self,
        event_type: AuditEventType,
        action: str,
        *,
        severity: AuditSeverity = AuditSeverity.INFO,
        trace_id: str = "",
        user_id: str | None = None,
        user_email: str | None = None,
        api_key_name: str | None = None,
        client_ip: str = "unknown",
        user_agent: str = "",
        resource: str = "",
        resource_id: str | None = None,
        http_method: str | None = None,
        http_path: str | None = None,
        http_status_code: int | None = None,
        http_query_params: dict[str, Any] | None = None,
        input_data: Any = None,
        output_data: Any = None,
        payload_size_bytes: int | None = None,
        trinity_score: float | None = None,
        risk_score: float | None = None,
        metadata: dict[str, Any] | None = None,
        duration_ms: float | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> AuditEvent | None:
        """Log an audit event

        Args:
            event_type: Type of audit event
            action: Description of the action
            severity: Event severity level
            trace_id: Request trace ID for correlation
            user_id: User ID if authenticated
            user_email: User email if available
            api_key_name: API key name if used
            client_ip: Client IP address
            user_agent: HTTP User-Agent header
            resource: Resource being accessed/modified
            resource_id: Specific resource identifier
            http_method: HTTP method
            http_path: HTTP request path
            http_status_code: HTTP response status code
            http_query_params: Query parameters (will be sanitized)
            input_data: Input data (will be hashed)
            output_data: Output data (will be hashed)
            payload_size_bytes: Request/response payload size
            trinity_score: Trinity Score if evaluated
            risk_score: Risk score if evaluated
            metadata: Additional event metadata
            duration_ms: Operation duration in milliseconds
            success: Whether the operation succeeded
            error_message: Error message if failed

        Returns:
            The created AuditEvent, or None if logging is disabled
        """
        if not self._enabled:
            return None

        # Hash input/output data if provided
        input_hash = self._hash_data(input_data) if input_data is not None else None
        output_hash = self._hash_data(output_data) if output_data is not None else None

        # Sanitize query params (remove sensitive data)
        sanitized_params = self._sanitize_params(http_query_params or {})

        event = AuditEvent(
            event_type=event_type,
            action=action,
            severity=severity,
            trace_id=trace_id,
            user_id=user_id,
            user_email=user_email,
            api_key_name=api_key_name,
            client_ip=client_ip,
            user_agent=user_agent,
            resource=resource,
            resource_id=resource_id,
            http_method=http_method,
            http_path=http_path,
            http_status_code=http_status_code,
            http_query_params=sanitized_params,
            input_hash=input_hash,
            output_hash=output_hash,
            payload_size_bytes=payload_size_bytes,
            trinity_score=trinity_score,
            risk_score=risk_score,
            metadata=metadata or {},
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
        )

        stored = await self._storage.store(event)
        if not stored:
            logger.warning(f"Failed to store audit event: {event.event_id}")

        return event

    async def log_http_request(
        self,
        request: Request,
        response: Response,
        duration_ms: float,
        *,
        user_id: str | None = None,
        api_key_name: str | None = None,
    ) -> AuditEvent | None:
        """Log an HTTP request/response cycle"""

        # Extract client IP
        client_ip = self._get_client_ip(request)

        # Determine severity based on status code
        status_code = response.status_code
        if status_code >= 500:
            severity = AuditSeverity.ERROR
        elif status_code >= 400:
            severity = AuditSeverity.WARNING
        else:
            severity = AuditSeverity.INFO

        return await self.log(
            event_type=AuditEventType.HTTP_REQUEST,
            action=f"{request.method} {request.url.path}",
            severity=severity,
            trace_id=getattr(request.state, "trace_id", ""),
            user_id=user_id,
            api_key_name=api_key_name,
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent", ""),
            resource=request.url.path,
            http_method=request.method,
            http_path=request.url.path,
            http_status_code=status_code,
            http_query_params=dict(request.query_params),
            duration_ms=duration_ms,
            success=status_code < 400,
        )

    async def log_auth_event(
        self,
        event_type: AuditEventType,
        action: str,
        *,
        user_id: str | None = None,
        user_email: str | None = None,
        client_ip: str = "unknown",
        success: bool = True,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent | None:
        """Log an authentication event"""
        severity = AuditSeverity.INFO if success else AuditSeverity.WARNING

        return await self.log(
            event_type=event_type,
            action=action,
            severity=severity,
            user_id=user_id,
            user_email=user_email,
            client_ip=client_ip,
            resource="auth",
            success=success,
            error_message=error_message,
            metadata=metadata or {},
        )

    async def log_data_operation(
        self,
        operation: str,
        resource: str,
        resource_id: str | None = None,
        *,
        user_id: str | None = None,
        input_data: Any = None,
        output_data: Any = None,
        success: bool = True,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent | None:
        """Log a data operation (CRUD)"""
        event_type_map = {
            "create": AuditEventType.DATA_CREATE,
            "read": AuditEventType.DATA_READ,
            "update": AuditEventType.DATA_UPDATE,
            "delete": AuditEventType.DATA_DELETE,
        }

        event_type = event_type_map.get(operation.lower(), AuditEventType.CUSTOM)
        severity = AuditSeverity.INFO if success else AuditSeverity.ERROR

        return await self.log(
            event_type=event_type,
            action=f"{operation.upper()} {resource}",
            severity=severity,
            user_id=user_id,
            resource=resource,
            resource_id=resource_id,
            input_data=input_data,
            output_data=output_data,
            success=success,
            error_message=error_message,
            metadata=metadata or {},
        )

    async def log_chancellor_decision(
        self,
        action: str,
        trinity_score: float,
        risk_score: float,
        decision: str,
        *,
        trace_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent | None:
        """Log a Chancellor Graph decision"""
        return await self.log(
            event_type=AuditEventType.CHANCELLOR_DECISION,
            action=action,
            severity=AuditSeverity.INFO,
            trace_id=trace_id,
            resource="chancellor_graph",
            trinity_score=trinity_score,
            risk_score=risk_score,
            metadata={
                "decision": decision,
                **(metadata or {}),
            },
        )

    async def log_security_event(
        self,
        event_type: AuditEventType,
        action: str,
        *,
        client_ip: str = "unknown",
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent | None:
        """Log a security-related event"""
        severity = (
            AuditSeverity.CRITICAL
            if event_type == AuditEventType.SECURITY_VIOLATION
            else AuditSeverity.WARNING
        )

        return await self.log(
            event_type=event_type,
            action=action,
            severity=severity,
            client_ip=client_ip,
            user_id=user_id,
            resource="security",
            metadata=metadata or {},
        )

    async def query(self, query: AuditQuery) -> list[AuditEvent]:
        """Query audit events"""
        return await self._storage.query(query)

    async def get_stats(self, hours: int = 24) -> AuditStats:
        """Get audit statistics"""
        return await self._storage.get_stats(hours)

    async def close(self) -> None:
        """Close the audit trail and storage"""
        await self._storage.close()

    def enable(self) -> None:
        """Enable audit logging"""
        self._enabled = True

    def disable(self) -> None:
        """Disable audit logging"""
        self._enabled = False

    @staticmethod
    def _hash_data(data: Any) -> str:
        """Create SHA256 hash of data"""
        try:
            import json

            if isinstance(data, (dict, list)):
                data_str = json.dumps(data, sort_keys=True, default=str)
            else:
                data_str = str(data)
            return hashlib.sha256(data_str.encode()).hexdigest()
        except Exception:
            return "hash_error"

    @staticmethod
    def _sanitize_params(params: dict[str, Any]) -> dict[str, Any]:
        """Sanitize query parameters by redacting sensitive values"""
        sensitive_keys = {"password", "token", "secret", "key", "auth", "credential", "api_key"}

        sanitized = {}
        for key, value in params.items():
            key_lower = key.lower()
            if any(s in key_lower for s in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        return sanitized

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract client IP from request"""
        # Check X-Forwarded-For header (for proxied requests)
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        x_real_ip = request.headers.get("x-real-ip")
        if x_real_ip:
            return x_real_ip

        # Fall back to client host
        if request.client:
            return request.client.host or "unknown"

        return "unknown"


# ============================================================================
# Global Instance & Convenience Functions
# ============================================================================


# Global audit trail instance
_audit_trail: AuditTrail | None = None


def get_audit_trail() -> AuditTrail:
    """Get the global audit trail instance"""
    global _audit_trail
    if _audit_trail is None:
        _audit_trail = AuditTrail()
    return _audit_trail


def set_audit_trail(audit_trail: AuditTrail) -> None:
    """Set the global audit trail instance (for testing)"""
    global _audit_trail
    _audit_trail = audit_trail
