"""Collaboration Models and Constants.

실시간 협업 시스템에 필요한 데이터 모델 및 상수 정의.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Participant:
    """협업 세션 참가자."""

    user_id: str
    role: str
    joined_at: datetime = field(default_factory=datetime.now)
    websocket: Any = None
    permissions: dict[str, str] = field(default_factory=dict)


@dataclass
class CollaborationSession:
    """협업 세션 모델."""

    session_id: str
    name: str
    creator_id: str
    session_type: str = "tax_analysis"
    max_participants: int = 5
    created_at: datetime = field(default_factory=datetime.now)
    participants: dict[str, Participant] = field(default_factory=dict)
    shared_documents: dict[str, dict[str, Any]] = field(default_factory=dict)
    operation_history: list[dict[str, Any]] = field(default_factory=list)
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Operation:
    """실시간 편집 작업(Operation)."""

    type: str  # 'insert', 'delete', 'update', 'style'
    user_id: str
    document_id: str
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    version: int = 0
