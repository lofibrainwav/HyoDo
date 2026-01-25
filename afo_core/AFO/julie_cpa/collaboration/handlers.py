"""
Julie CPA Collaboration Handlers

메시지 핸들러 모듈
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from .models import CollaborationMessage

if TYPE_CHECKING:
    from .hub import JulieCPAAgentCollaborationHub

logger = logging.getLogger(__name__)


class MessageHandlers:
    """메시지 핸들러 클래스"""

    def __init__(self, hub: "JulieCPAAgentCollaborationHub") -> None:
        self.hub = hub

    async def handle_trinity_score_update(self, message: CollaborationMessage) -> None:
        """Trinity Score 업데이트 처리"""
        session_id = message.session_id
        agent_type = message.sender_agent
        new_score = message.payload.get("trinity_score")

        if not new_score:
            return

        # Trinity Score 풀 업데이트
        if session_id not in self.hub.trinity_score_pool:
            self.hub.trinity_score_pool[session_id] = {}

        self.hub.trinity_score_pool[session_id][agent_type] = new_score

        # 다른 Agent들에게 브로드캐스트
        broadcast_message = CollaborationMessage(
            message_id=str(uuid.uuid4()),
            message_type="trinity_score_sync",
            sender_agent="hub",
            target_agents=["associate", "manager", "auditor"],
            payload={
                "updated_agent": agent_type,
                "new_score": new_score,
                "full_pool": self.hub.trinity_score_pool.get(session_id, {}),
            },
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
        )

        await self.hub._broadcast_to_session(
            session_id, broadcast_message, exclude_agent=agent_type
        )
        self.hub.collaboration_stats["trinity_score_updates"] += 1

        logger.info(f"Trinity Score updated for {agent_type}: {new_score}")

    async def handle_agent_request(self, message: CollaborationMessage) -> None:
        """Agent 요청 처리"""
        request_type = message.payload.get("request_type")
        target_agent = message.payload.get("target_agent")
        request_data = message.payload.get("request_data", {})

        if not target_agent or target_agent not in self.hub.agents:
            error_response = CollaborationMessage(
                message_id=str(uuid.uuid4()),
                message_type="agent_response",
                sender_agent="hub",
                target_agents=[message.sender_agent],
                payload={
                    "request_id": message.message_id,
                    "status": "error",
                    "error": f"Unknown target agent: {target_agent}",
                },
                timestamp=datetime.now().isoformat(),
                session_id=message.session_id,
            )
            await self.hub._send_message_to_agent(message.sender_agent, error_response)
            return

        forwarded_request = CollaborationMessage(
            message_id=str(uuid.uuid4()),
            message_type="agent_request_forwarded",
            sender_agent=message.sender_agent,
            target_agents=[target_agent],
            payload={
                "original_request_id": message.message_id,
                "request_type": request_type,
                "request_data": request_data,
            },
            timestamp=datetime.now().isoformat(),
            session_id=message.session_id,
        )

        await self.hub._send_message_to_agent(target_agent, forwarded_request)

    async def handle_irs_change_alert(self, message: CollaborationMessage) -> None:
        """IRS 변경 알림 처리"""
        change_data = message.payload

        alert_message = CollaborationMessage(
            message_id=str(uuid.uuid4()),
            message_type="irs_change_notification",
            sender_agent="hub",
            target_agents=list(self.hub.irs_change_listeners),
            payload=change_data,
            timestamp=datetime.now().isoformat(),
            session_id=message.session_id,
            priority="high",
        )

        await self.hub._broadcast_to_agents(list(self.hub.irs_change_listeners), alert_message)
        self.hub.collaboration_stats["irs_updates_broadcasted"] += 1

        logger.info(f"IRS change alert broadcasted to {len(self.hub.irs_change_listeners)} agents")

    async def handle_collaboration_request(self, message: CollaborationMessage) -> None:
        """협업 요청 처리"""
        collaboration_type = message.payload.get("collaboration_type")

        if collaboration_type == "parallel_analysis":
            await self._initiate_parallel_analysis(message)
        elif collaboration_type == "trinity_score_review":
            await self._initiate_trinity_score_review(message)
        elif collaboration_type == "evidence_sharing":
            await self._initiate_evidence_sharing(message)
        else:
            logger.warning(f"Unknown collaboration type: {collaboration_type}")

    async def handle_session_command(self, message: CollaborationMessage) -> None:
        """세션 명령 처리"""
        command = message.payload.get("command")

        if command == "pause_session":
            await self.hub._pause_session(message.session_id)
        elif command == "resume_session":
            await self.hub._resume_session(message.session_id)
        elif command == "end_session":
            await self.hub._end_session(message.session_id)
        else:
            logger.warning(f"Unknown session command: {command}")

    async def _initiate_parallel_analysis(self, message: CollaborationMessage) -> None:
        """병렬 분석 협업 시작"""
        session_id = message.session_id
        analysis_data = message.payload.get("analysis_data", {})

        analysis_request = CollaborationMessage(
            message_id=str(uuid.uuid4()),
            message_type="parallel_analysis_request",
            sender_agent="hub",
            target_agents=["associate", "manager", "auditor"],
            payload={
                "analysis_type": analysis_data.get("type", "general"),
                "data": analysis_data,
                "collaboration_id": str(uuid.uuid4()),
            },
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
        )

        await self.hub._broadcast_to_session(session_id, analysis_request)

        result_collector = asyncio.create_task(
            self._collect_parallel_analysis_results(session_id, analysis_request.message_id)
        )
        self.hub.message_processors[f"analysis_{session_id}"] = result_collector

    async def _collect_parallel_analysis_results(self, session_id: str, request_id: str) -> None:
        """병렬 분석 결과 수집"""
        results: dict[str, Any] = {}
        timeout = 300

        try:
            start_time = asyncio.get_event_loop().time()

            while asyncio.get_event_loop().time() - start_time < timeout:
                await asyncio.sleep(1)
                if len(results) >= 3:
                    break

            consolidated_result = self._consolidate_analysis_results(results)

            result_message = CollaborationMessage(
                message_id=str(uuid.uuid4()),
                message_type="parallel_analysis_complete",
                sender_agent="hub",
                target_agents=["associate", "manager", "auditor"],
                payload={
                    "request_id": request_id,
                    "consolidated_result": consolidated_result,
                    "individual_results": results,
                },
                timestamp=datetime.now().isoformat(),
                session_id=session_id,
            )

            await self.hub._broadcast_to_session(session_id, result_message)

        except Exception as e:
            logger.error(f"Error collecting parallel analysis results: {e}")

    def _consolidate_analysis_results(self, results: dict[str, Any]) -> dict[str, Any]:
        """분석 결과 종합"""
        consolidated = {
            "total_contributions": len(results),
            "consensus_level": "high" if len(results) >= 2 else "low",
            "key_findings": [],
            "recommendations": [],
        }

        trinity_scores = self.hub.trinity_score_pool.get("session_id", {})
        weighted_score = sum(
            result.get("confidence", 0.5) * trinity_scores.get(agent_type, 1.0)
            for agent_type, result in results.items()
        ) / max(len(results), 1)

        consolidated["weighted_confidence"] = weighted_score
        return consolidated

    async def _initiate_trinity_score_review(self, _message: CollaborationMessage) -> None:
        """Trinity Score 리뷰 시작 (구현 예정)"""
        pass

    async def _initiate_evidence_sharing(self, _message: CollaborationMessage) -> None:
        """증거 공유 시작 (구현 예정)"""
        pass
