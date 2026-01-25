"""
Julie CPA Collaboration Models

협업 시스템용 데이터 모델 정의
"""

from dataclasses import dataclass
from typing import Any

from fastapi import WebSocket


@dataclass
class CollaborationMessage:
    """협업 메시지 데이터 클래스"""

    message_id: str
    message_type: str  # 'trinity_score_update', 'agent_request', 'irs_update', etc.
    sender_agent: str
    target_agents: list[str]
    payload: dict[str, Any]
    timestamp: str
    session_id: str
    priority: str = "normal"  # 'low', 'normal', 'high', 'urgent'


@dataclass
class CollaborationSession:
    """협업 세션 정보"""

    session_id: str
    client_id: str
    active_agents: dict[str, Any]
    websocket_connections: dict[str, WebSocket]
    trinity_score_pool: dict[str, float]
    session_start_time: str
    last_activity: str
    status: str = "active"  # 'active', 'paused', 'completed'
