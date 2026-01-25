# Trinity Score: 96.0 (Phase 33 Audit Module Refactoring)
"""Audit Models and Data Structures"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# Enums & Constants (眞 - Truth)
# ============================================================================


class AuditEventType(str, Enum):
    """Audit event types (眞 - Classification)"""

    # HTTP Request Events
    HTTP_REQUEST = "http_request"
    HTTP_RESPONSE = "http_response"

    # Authentication Events
    AUTH_LOGIN = "auth_login"
    AUTH_LOGOUT = "auth_logout"
    AUTH_FAILED = "auth_failed"
    AUTH_TOKEN_REFRESH = "auth_token_refresh"  # noqa: S105

    # Data Operations
    DATA_CREATE = "data_create"
    DATA_READ = "data_read"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"

    # System Events
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
    SYSTEM_INFO = "system_info"

    # Security Events
    SECURITY_VIOLATION = "security_violation"
    SECURITY_ALERT = "security_alert"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

    # Chancellor Graph Events
    CHANCELLOR_DECISION = "chancellor_decision"
    TRINITY_SCORE_EVALUATION = "trinity_score_evaluation"

    # Custom Event
    CUSTOM = "custom"


class AuditSeverity(str, Enum):
    """Audit event severity levels (善 - Importance)"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================================
# Pydantic Models (善 - Goodness)
# ============================================================================


class AuditEvent(BaseModel):
    """Audit event model (眞善美 - Complete Record)

    Immutable record of an auditable action in the system.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        validate_default=True,
    )

    # Core Identifiers
    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique event identifier"
    )
    trace_id: str = Field(default="", description="Request trace ID for correlation")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Event timestamp (UTC)"
    )

    # Event Classification
    event_type: AuditEventType = Field(..., description="Type of audit event")
    severity: AuditSeverity = Field(default=AuditSeverity.INFO, description="Event severity level")

    # Actor Information
    user_id: str | None = Field(default=None, description="User ID if authenticated")
    user_email: str | None = Field(default=None, description="User email if available")
    api_key_name: str | None = Field(default=None, description="API key name if used")
    client_ip: str = Field(default="unknown", description="Client IP address")
    user_agent: str = Field(default="", description="HTTP User-Agent header")

    # Action Details
    action: str = Field(..., description="Description of the action performed")
    resource: str = Field(default="", description="Resource being accessed/modified")
    resource_id: str | None = Field(default=None, description="Specific resource identifier")

    # HTTP Context (if applicable)
    http_method: str | None = Field(default=None, description="HTTP method (GET, POST, etc.)")
    http_path: str | None = Field(default=None, description="HTTP request path")
    http_status_code: int | None = Field(default=None, description="HTTP response status code")
    http_query_params: dict[str, Any] = Field(
        default_factory=dict, description="Query parameters (sanitized)"
    )

    # Data Context
    input_hash: str | None = Field(default=None, description="SHA256 hash of input data")
    output_hash: str | None = Field(default=None, description="SHA256 hash of output data")
    payload_size_bytes: int | None = Field(
        default=None, description="Request/response payload size"
    )

    # Trinity Score Context
    trinity_score: float | None = Field(default=None, description="Trinity Score if evaluated")
    risk_score: float | None = Field(default=None, description="Risk score if evaluated")

    # Additional Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional event metadata")
    duration_ms: float | None = Field(
        default=None, description="Operation duration in milliseconds"
    )

    # Outcome
    success: bool = Field(default=True, description="Whether the operation succeeded")
    error_message: str | None = Field(default=None, description="Error message if failed")

    def to_json(self) -> str:
        """Serialize to JSON string"""
        return self.model_dump_json()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary with datetime conversion"""
        data = self.model_dump()
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditEvent:
        """Create event from dictionary"""
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class AuditQuery(BaseModel):
    """Query parameters for audit log search"""

    model_config = ConfigDict(extra="forbid")

    event_types: list[AuditEventType] | None = None
    severities: list[AuditSeverity] | None = None
    user_id: str | None = None
    trace_id: str | None = None
    resource: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    success: bool | None = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


class AuditStats(BaseModel):
    """Audit statistics model"""

    total_events: int = 0
    events_by_type: dict[str, int] = Field(default_factory=dict)
    events_by_severity: dict[str, int] = Field(default_factory=dict)
    unique_users: int = 0
    unique_resources: int = 0
    success_rate: float = 0.0
    time_range_hours: int = 24
