"""
Julie CPA Collaboration Module

협업 허브 시스템 메인 진입점
"""

from typing import Any

from fastapi import WebSocket

from .hub import JulieCPAAgentCollaborationHub
from .models import CollaborationMessage, CollaborationSession

__all__ = [
    "JulieCPAAgentCollaborationHub",
    "CollaborationMessage",
    "CollaborationSession",
    "collaboration_hub",
    "start_collaboration_hub",
    "stop_collaboration_hub",
    "get_collaboration_stats",
    "register_agent_connection",
    "unregister_agent_connection",
    "handle_agent_message",
]

# 글로벌 인스턴스
collaboration_hub = JulieCPAAgentCollaborationHub()


# 편의 함수들
async def start_collaboration_hub() -> None:
    """협업 허브 시작"""
    await collaboration_hub.start_hub()


async def stop_collaboration_hub() -> None:
    """협업 허브 중지"""
    await collaboration_hub.stop_hub()


def get_collaboration_stats() -> dict[str, Any]:
    """협업 통계 조회"""
    return collaboration_hub.get_collaboration_stats()


async def register_agent_connection(agent_type: str, websocket: WebSocket, client_id: str) -> str:
    """Agent 연결 등록"""
    return await collaboration_hub.register_agent_connection(agent_type, websocket, client_id)


async def unregister_agent_connection(connection_id: str) -> None:
    """Agent 연결 해제"""
    await collaboration_hub.unregister_agent_connection(connection_id)


async def handle_agent_message(agent_type: str, message_data: dict[str, Any]) -> None:
    """Agent 메시지 처리"""
    await collaboration_hub.handle_agent_message(agent_type, message_data)
