"""
Julie CPA Agent Collaboration Hub

Julie CPA Agent 간 실시간 협업을 위한 중앙 허브 시스템
"""

import asyncio
import logging
import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Any

from fastapi import WebSocket

from AFO.julie_cpa_agents import JulieAssociateAgent, JulieAuditorAgent, JulieManagerAgent

from .handlers import MessageHandlers
from .models import CollaborationMessage, CollaborationSession

logger = logging.getLogger(__name__)


class JulieCPAAgentCollaborationHub:
    """
    Julie CPA Agent 협업 허브

    주요 기능:
    - 실시간 WebSocket 통신 관리
    - Agent 등록 및 상태 관리
    - Trinity Score 공유 및 동기화
    - 협업 워크플로우 조율
    - IRS 변경 알림 브로드캐스트
    """

    def __init__(self) -> None:
        self.agents = {
            "associate": JulieAssociateAgent(),
            "manager": JulieManagerAgent(),
            "auditor": JulieAuditorAgent(),
        }

        self.active_sessions: dict[str, CollaborationSession] = {}
        self.websocket_connections: dict[str, WebSocket] = {}
        self.message_queue: asyncio.Queue[CollaborationMessage] = asyncio.Queue()
        self.message_processors: dict[str, asyncio.Task[Any]] = {}
        self.trinity_score_pool: dict[str, dict[str, float]] = {}
        self.score_sync_tasks: dict[str, asyncio.Task[Any]] = {}
        self.irs_change_listeners: set[str] = set()

        self.collaboration_stats = {
            "total_sessions": 0,
            "active_connections": 0,
            "messages_processed": 0,
            "trinity_score_updates": 0,
            "irs_updates_broadcasted": 0,
            "errors_handled": 0,
        }

        self._handlers = MessageHandlers(self)
        logger.info("Julie CPA Agent Collaboration Hub initialized")

    async def start_hub(self) -> None:
        """협업 허브 시작"""
        logger.info("Starting Julie CPA Agent Collaboration Hub...")

        message_processor = asyncio.create_task(self._process_messages())
        self.message_processors["main"] = message_processor

        cleanup_task = asyncio.create_task(self._cleanup_inactive_sessions())
        self.message_processors["cleanup"] = cleanup_task

        logger.info("Julie CPA Agent Collaboration Hub started successfully")

    async def stop_hub(self) -> None:
        """협업 허브 중지"""
        logger.info("Stopping Julie CPA Agent Collaboration Hub...")

        for _task_name, task in self.message_processors.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        for connection_id, websocket in self.websocket_connections.items():
            try:
                await websocket.close()
            except Exception as e:
                logger.warning(f"Error closing websocket {connection_id}: {e}")

        self.active_sessions.clear()
        self.websocket_connections.clear()
        logger.info("Julie CPA Agent Collaboration Hub stopped")

    async def register_agent_connection(
        self, agent_type: str, websocket: WebSocket, client_id: str
    ) -> str:
        """Agent WebSocket 연결 등록"""
        connection_id = f"{agent_type}_{client_id}_{uuid.uuid4().hex[:8]}"

        existing_connections = [
            conn_id
            for conn_id, _conn in self.websocket_connections.items()
            if conn_id.startswith(f"{agent_type}_{client_id}")
        ]
        for conn_id in existing_connections:
            try:
                await self.websocket_connections[conn_id].close()
            except Exception:
                pass
            del self.websocket_connections[conn_id]

        self.websocket_connections[connection_id] = websocket
        session_id = await self._ensure_session_exists(client_id)

        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.active_agents[agent_type] = {
                "connection_id": connection_id,
                "status": "connected",
                "last_seen": datetime.now().isoformat(),
            }
            session.websocket_connections[agent_type] = websocket

        welcome_message = CollaborationMessage(
            message_id=str(uuid.uuid4()),
            message_type="agent_connected",
            sender_agent="hub",
            target_agents=[agent_type],
            payload={
                "connection_id": connection_id,
                "session_id": session_id,
                "hub_status": "ready",
                "available_agents": list(self.agents.keys()),
            },
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
        )

        await self._send_message_to_agent(agent_type, welcome_message)
        self.collaboration_stats["active_connections"] += 1
        logger.info(f"Agent {agent_type} connected: {connection_id}")

        return connection_id

    async def unregister_agent_connection(self, connection_id: str) -> None:
        """Agent 연결 해제"""
        if connection_id in self.websocket_connections:
            websocket = self.websocket_connections[connection_id]

            try:
                await websocket.close()
            except Exception as e:
                logger.warning(f"Error closing websocket {connection_id}: {e}")

            del self.websocket_connections[connection_id]

            for _session_id, session in self.active_sessions.items():
                for _agent_type, agent_info in session.active_agents.items():
                    if agent_info.get("connection_id") == connection_id:
                        agent_info["status"] = "disconnected"
                        agent_info["disconnected_at"] = datetime.now().isoformat()
                        break

            self.collaboration_stats["active_connections"] -= 1
            logger.info(f"Agent connection unregistered: {connection_id}")

    async def handle_agent_message(self, agent_type: str, message_data: dict[str, Any]) -> None:
        """Agent로부터 수신된 메시지 처리"""
        try:
            message = CollaborationMessage(**message_data)
            await self.message_queue.put(message)
            self.collaboration_stats["messages_processed"] += 1
            logger.debug(f"Message queued from {agent_type}: {message.message_type}")
        except Exception as e:
            logger.error(f"Error handling message from {agent_type}: {e}")

    async def _process_messages(self) -> None:
        """메시지 큐 처리 메인 루프"""
        while True:
            try:
                message = await self.message_queue.get()

                if message.message_type == "trinity_score_update":
                    await self._handlers.handle_trinity_score_update(message)
                elif message.message_type == "agent_request":
                    await self._handlers.handle_agent_request(message)
                elif message.message_type == "irs_change_alert":
                    await self._handlers.handle_irs_change_alert(message)
                elif message.message_type == "collaboration_request":
                    await self._handlers.handle_collaboration_request(message)
                elif message.message_type == "session_command":
                    await self._handlers.handle_session_command(message)
                else:
                    logger.warning(f"Unknown message type: {message.message_type}")

                self.message_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                self.collaboration_stats["errors_handled"] += 1

    async def _ensure_session_exists(self, client_id: str) -> str:
        """클라이언트 세션 존재 확인 및 생성"""
        for session_id, session in self.active_sessions.items():
            if session.client_id == client_id and session.status == "active":
                return session_id

        session_id = f"session_{client_id}_{uuid.uuid4().hex[:8]}"

        new_session = CollaborationSession(
            session_id=session_id,
            client_id=client_id,
            active_agents={},
            websocket_connections={},
            trinity_score_pool={},
            session_start_time=datetime.now().isoformat(),
            last_activity=datetime.now().isoformat(),
        )

        self.active_sessions[session_id] = new_session
        self.collaboration_stats["total_sessions"] += 1

        logger.info(f"New collaboration session created: {session_id}")
        return session_id

    async def _send_message_to_agent(self, agent_type: str, message: CollaborationMessage) -> None:
        """특정 Agent에게 메시지 전송"""
        for session in self.active_sessions.values():
            if agent_type in session.websocket_connections:
                websocket = session.websocket_connections[agent_type]
                try:
                    await websocket.send_json(asdict(message))
                    return
                except Exception as e:
                    logger.error(f"Error sending message to {agent_type}: {e}")
                    if agent_type in session.active_agents:
                        session.active_agents[agent_type]["status"] = "disconnected"

        logger.warning(f"No active connection found for agent: {agent_type}")

    async def _broadcast_to_session(
        self, session_id: str, message: CollaborationMessage, exclude_agent: str | None = None
    ) -> None:
        """세션 내 모든 Agent에게 메시지 브로드캐스트"""
        if session_id not in self.active_sessions:
            return

        session = self.active_sessions[session_id]

        for agent_type, websocket in session.websocket_connections.items():
            if exclude_agent and agent_type == exclude_agent:
                continue

            try:
                await websocket.send_json(asdict(message))
            except Exception as e:
                logger.error(f"Error broadcasting to {agent_type}: {e}")

    async def _broadcast_to_agents(
        self, agent_types: list[str], message: CollaborationMessage
    ) -> None:
        """특정 Agent들에게 메시지 브로드캐스트"""
        for agent_type in agent_types:
            await self._send_message_to_agent(agent_type, message)

    async def _cleanup_inactive_sessions(self) -> None:
        """비활성 세션 정리"""
        while True:
            try:
                await asyncio.sleep(300)
                current_time = datetime.now()
                inactive_sessions = []

                for session_id, session in self.active_sessions.items():
                    last_activity = datetime.fromisoformat(session.last_activity)
                    if (current_time - last_activity).total_seconds() > 1800:
                        inactive_sessions.append(session_id)

                for session_id in inactive_sessions:
                    session = self.active_sessions[session_id]
                    logger.info(f"Cleaning up inactive session: {session_id}")

                    for websocket in session.websocket_connections.values():
                        try:
                            await websocket.close()
                        except Exception:
                            pass

                    del self.active_sessions[session_id]

                    if session_id in self.trinity_score_pool:
                        del self.trinity_score_pool[session_id]

                if inactive_sessions:
                    logger.info(f"Cleaned up {len(inactive_sessions)} inactive sessions")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")

    async def _pause_session(self, session_id: str) -> None:
        """세션 일시 중지"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].status = "paused"
            logger.info(f"Session paused: {session_id}")

    async def _resume_session(self, session_id: str) -> None:
        """세션 재개"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].status = "active"
            self.active_sessions[session_id].last_activity = datetime.now().isoformat()
            logger.info(f"Session resumed: {session_id}")

    async def _end_session(self, session_id: str) -> None:
        """세션 종료"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.status = "completed"

            for websocket in session.websocket_connections.values():
                try:
                    await websocket.close()
                except Exception:
                    pass

            logger.info(f"Session ended: {session_id}")

    def register_irs_change_listener(self, agent_type: str) -> None:
        """IRS 변경 리스너 등록"""
        self.irs_change_listeners.add(agent_type)
        logger.info(f"IRS change listener registered: {agent_type}")

    def unregister_irs_change_listener(self, agent_type: str) -> None:
        """IRS 변경 리스너 해제"""
        self.irs_change_listeners.discard(agent_type)
        logger.info(f"IRS change listener unregistered: {agent_type}")

    def get_collaboration_stats(self) -> dict[str, Any]:
        """협업 통계 조회"""
        return {
            "active_sessions": len(self.active_sessions),
            "active_connections": self.collaboration_stats["active_connections"],
            "total_sessions_created": self.collaboration_stats["total_sessions"],
            "messages_processed": self.collaboration_stats["messages_processed"],
            "trinity_score_updates": self.collaboration_stats["trinity_score_updates"],
            "irs_updates_broadcasted": self.collaboration_stats["irs_updates_broadcasted"],
            "errors_handled": self.collaboration_stats["errors_handled"],
            "registered_listeners": len(self.irs_change_listeners),
        }

    def get_session_info(self, session_id: str) -> dict[str, Any] | None:
        """세션 정보 조회"""
        if session_id not in self.active_sessions:
            return None

        session = self.active_sessions[session_id]
        return {
            "session_id": session.session_id,
            "client_id": session.client_id,
            "status": session.status,
            "active_agents": list(session.active_agents.keys()),
            "start_time": session.session_start_time,
            "last_activity": session.last_activity,
            "trinity_scores": self.trinity_score_pool.get(session_id, {}),
        }
