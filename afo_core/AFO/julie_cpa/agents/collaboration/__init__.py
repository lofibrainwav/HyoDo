"""Real-time Collaboration System Package.

다중 CPA 실시간 협업 플랫폼.
WebSocket 기반 공유 작업 및 실시간 동기화 지원.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import CollaborationSession, Operation, Participant
from .ot_engine import OTEngine, apply_operation_to_doc
from .session_manager import SessionManager


class RealtimeCollaborationSystem:
    """실시간 협업 시스템 (Facade)."""

    def __init__(self) -> None:
        self.manager = SessionManager()
        self.ot_engine = OTEngine()

    async def create_collaboration_session(
        self,
        session_name: str,
        creator_id: str,
        session_type: str = "tax_analysis",
        max_participants: int = 5,
        _permissions: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """새로운 협업 세션 생성."""
        session = self.manager.create_session(
            session_name, creator_id, session_type, max_participants
        )

        return {
            "success": True,
            "session_id": session.session_id,
            "name": session.name,
            "creator_id": session.creator_id,
            "created_at": session.created_at.isoformat(),
        }

    async def join_collaboration_session(
        self,
        session_id: str,
        user_id: str,
        user_role: str = "participant",
        websocket_connection=None,
    ) -> dict[str, Any]:
        """협업 세션 참가."""
        session = self.manager.join_session(session_id, user_id, user_role)

        if not session:
            return {"success": False, "error": "Session not found or full"}

        # WebSocket 연결 저장 (실제 구현 시 필요)
        if websocket_connection:
            session.participants[user_id].websocket = websocket_connection

        return {
            "success": True,
            "session_id": session.session_id,
            "participants": [p.user_id for p in session.participants.values()],
            "status": session.status,
        }

    async def apply_operational_transform(
        self,
        session_id: str,
        user_id: str,
        document_id: str,
        operation: dict[str, Any],
    ) -> dict[str, Any]:
        """운영 변환(Operational Transform) 적용 및 브로드캐스트."""
        session = self.manager.get_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        # 히스토리 기반 변환 수행
        transformed_op = self.ot_engine.transform_operation(operation, session.operation_history)

        # 문서에 적용
        doc = session.shared_documents.get(document_id, {})
        session.shared_documents[document_id] = apply_operation_to_doc(doc, transformed_op)

        # 히스토리에 기록
        session.operation_history.append(transformed_op)

        return {
            "success": True,
            "applied_operation": transformed_op,
            "document_id": document_id,
            "version": len(session.operation_history),
        }

    async def get_session_status(self, session_id: str) -> dict[str, Any]:
        """세션 상태 조회."""
        session = self.manager.get_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        return {
            "session_id": session.session_id,
            "active_participants": len(session.participants),
            "status": session.status,
            "last_operation_at": session.operation_history[-1].get("timestamp")
            if session.operation_history
            else None,
        }

    async def leave_collaboration_session(self, session_id: str, user_id: str) -> dict[str, Any]:
        """협업 세션 퇴장."""
        success = self.manager.leave_session(session_id, user_id)
        return {"success": success}


__all__ = ["RealtimeCollaborationSystem", "CollaborationSession", "Participant", "Operation"]
