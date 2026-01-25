"""Collaboration Session Manager.

세션 생성, 참가, 퇴장 및 상태 관리.
"""

from __future__ import annotations

import uuid

from .models import CollaborationSession, Participant


class SessionManager:
    """협업 세션 관리자."""

    def __init__(self) -> None:
        self.sessions: dict[str, CollaborationSession] = {}

    def create_session(
        self,
        name: str,
        creator_id: str,
        session_type: str = "tax_analysis",
        max_participants: int = 5,
    ) -> CollaborationSession:
        """새로운 협업 세션을 생성합니다."""
        session_id = str(uuid.uuid4())
        session = CollaborationSession(
            session_id=session_id,
            name=name,
            creator_id=creator_id,
            session_type=session_type,
            max_participants=max_participants,
        )

        # 생성자를 첫 번째 참가자로 추가
        session.participants[creator_id] = Participant(user_id=creator_id, role="admin")

        self.sessions[session_id] = session
        return session

    def join_session(
        self, session_id: str, user_id: str, user_role: str = "participant"
    ) -> CollaborationSession | None:
        """기존 세션에 참가합니다."""
        session = self.sessions.get(session_id)
        if not session:
            return None

        if len(session.participants) >= session.max_participants:
            return None

        session.participants[user_id] = Participant(user_id=user_id, role=user_role)
        return session

    def leave_session(self, session_id: str, user_id: str) -> bool:
        """세션에서 퇴장합니다."""
        session = self.sessions.get(session_id)
        if not session or user_id not in session.participants:
            return False

        del session.participants[user_id]

        # 참가자가 없으면 세션 종료
        if not session.participants:
            session.status = "closed"

        return True

    def get_session(self, session_id: str) -> CollaborationSession | None:
        """세션 정보를 조회합니다."""
        return self.sessions.get(session_id)
