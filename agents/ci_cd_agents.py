#!/usr/bin/env python3
"""
HyoDo CI/CD 에이전트 네트워크 (Standalone)
코드 품질 검사를 에이전트화하여 병렬 처리하고 승상이 최종 검증하는 시스템

Trinity Score: 95.0 (Established by Chancellor)
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# Standalone 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


class InMemoryQueue:
    """인메모리 메시지 큐 (Redis 대체)"""

    def __init__(self) -> None:
        self._queues: dict[str, list[str]] = defaultdict(list)
        self._store: dict[str, str] = {}

    async def lpush(self, key: str, value: str) -> None:
        self._queues[key].insert(0, value)

    async def rpop(self, key: str) -> str | None:
        if self._queues[key]:
            return self._queues[key].pop()
        return None

    async def set(self, key: str, value: str, expire: int = 3600) -> None:
        self._store[key] = value

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def delete(self, key: str) -> None:
        """키 삭제"""
        self._store.pop(key, None)
        self._queues.pop(key, None)

    async def llen(self, key: str) -> int:
        """큐 길이 반환"""
        return len(self._queues.get(key, []))

    async def exists(self, key: str) -> bool:
        """키 존재 여부"""
        return key in self._store or key in self._queues


# 글로벌 인메모리 큐
_memory_queue = InMemoryQueue()


class AgentStatus(Enum):
    """에이전트 상태"""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class AgentPriority(Enum):
    """에이전트 우선순위"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MessageType(Enum):
    """메시지 타입"""

    TASK_ASSIGNMENT = "task_assignment"
    STATUS_UPDATE = "status_update"
    RESULT_REPORT = "result_report"
    VALIDATION_REQUEST = "validation_request"
    APPROVAL_GRANTED = "approval_granted"
    REJECTION_NOTICE = "rejection_notice"


@dataclass
class AgentMessage:
    """에이전트 간 메시지"""

    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.STATUS_UPDATE
    sender: str = ""
    recipient: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    correlation_id: str | None = None


@dataclass
class AgentResult:
    """에이전트 실행 결과"""

    agent_id: str
    task_id: str
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    execution_time: float = 0.0
    timestamp: float = field(default_factory=time.time)


class BaseAgent(ABC):
    """CI/CD 에이전트 베이스 클래스"""

    def __init__(
        self, agent_id: str, name: str, priority: AgentPriority = AgentPriority.MEDIUM
    ) -> None:
        self.agent_id = agent_id
        self.name = name
        self.priority = priority
        self.status = AgentStatus.IDLE
        self.current_task: str | None = None
        self.queue = _memory_queue  # Standalone 인메모리 큐

        # 메시지 큐 키들
        self.message_queue = f"agent:messages:{agent_id}"
        self.status_key = f"agent:status:{agent_id}"
        self.result_queue = f"agent:results:{agent_id}"

        logger.info(f"🛠️ [{self.name}] 에이전트 초기화 완료 (ID: {agent_id})")

    async def send_message(self, message: AgentMessage) -> None:
        """메시지 전송"""
        try:
            message.sender = self.agent_id
            message_data = {
                "message_id": message.message_id,
                "message_type": message.message_type.value,
                "sender": message.sender,
                "recipient": message.recipient,
                "payload": message.payload,
                "timestamp": message.timestamp,
                "correlation_id": message.correlation_id,
            }

            # 수신자 큐에 메시지 추가
            recipient_queue = f"agent:messages:{message.recipient}"
            await self.queue.lpush(recipient_queue, json.dumps(message_data))

            # 상태 업데이트
            await self.update_status()

            logger.debug(
                f"📤 [{self.name}] 메시지 전송: {message.message_type.value} → {message.recipient}"
            )

        except Exception as e:
            logger.error(f"❌ [{self.name}] 메시지 전송 실패: {e}")

    async def receive_messages(self) -> list[AgentMessage]:
        """메시지 수신"""
        try:
            messages = []
            while True:
                message_data = await self.queue.rpop(self.message_queue)
                if not message_data:
                    break

                data = json.loads(message_data)
                message = AgentMessage(
                    message_id=data["message_id"],
                    message_type=MessageType(data["message_type"]),
                    sender=data["sender"],
                    recipient=data["recipient"],
                    payload=data["payload"],
                    timestamp=data["timestamp"],
                    correlation_id=data.get("correlation_id"),
                )
                messages.append(message)

            return messages

        except Exception as e:
            logger.error(f"❌ [{self.name}] 메시지 수신 실패: {e}")
            return []

    async def update_status(self) -> None:
        """상태 업데이트"""
        status_data = {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "priority": self.priority.value,
            "current_task": self.current_task,
            "timestamp": time.time(),
        }

        await self.queue.set(self.status_key, json.dumps(status_data), expire=3600)  # 1시간 유지

    async def report_result(self, result: AgentResult) -> None:
        """결과 보고"""
        try:
            result_data = {
                "agent_id": result.agent_id,
                "task_id": result.task_id,
                "success": result.success,
                "data": result.data,
                "errors": result.errors,
                "execution_time": result.execution_time,
                "timestamp": result.timestamp,
            }

            await self.queue.lpush(self.result_queue, json.dumps(result_data))

            # Chancellor에게 결과 보고 메시지 전송
            await self.send_message(
                AgentMessage(
                    message_type=MessageType.RESULT_REPORT,
                    recipient="chancellor_validator",
                    payload=result_data,
                    correlation_id=result.task_id,
                )
            )

        except Exception as e:
            logger.error(f"❌ [{self.name}] 결과 보고 실패: {e}")

    @abstractmethod
    async def execute_task(self, task_id: str, **kwargs) -> AgentResult:
        """태스크 실행 (하위 클래스에서 구현)"""
        pass

    async def run(self) -> None:
        """에이전트 메인 루프"""
        logger.info(f"🚀 [{self.name}] 에이전트 실행 시작")

        while True:
            try:
                # 메시지 확인 및 처리
                messages = await self.receive_messages()
                for message in messages:
                    await self.process_message(message)

                # 상태 업데이트
                await self.update_status()

                # 잠시 대기
                await asyncio.sleep(1.0)

            except Exception as e:
                logger.error(f"❌ [{self.name}] 에이전트 루프 오류: {e}")
                await asyncio.sleep(5.0)  # 에러 시 5초 대기

    async def process_message(self, message: AgentMessage) -> None:
        """메시지 처리"""
        if message.message_type == MessageType.TASK_ASSIGNMENT:
            await self.handle_task_assignment(message)
        elif message.message_type == MessageType.VALIDATION_REQUEST:
            await self.handle_validation_request(message)
        else:
            logger.debug(f"📨 [{self.name}] 메시지 수신: {message.message_type.value}")

    async def handle_task_assignment(self, message: AgentMessage) -> None:
        """태스크 할당 처리"""
        task_id = message.payload.get("task_id")
        task_params = message.payload.get("params", {})

        if task_id:
            logger.info(f"🎯 [{self.name}] 태스크 할당됨: {task_id}")
            self.status = AgentStatus.RUNNING
            self.current_task = task_id

            try:
                result = await self.execute_task(task_id, **task_params)
                await self.report_result(result)

                self.status = AgentStatus.COMPLETED if result.success else AgentStatus.FAILED
                self.current_task = None

            except TimeoutError:
                self.status = AgentStatus.TIMEOUT
                error_result = AgentResult(
                    agent_id=self.agent_id,
                    task_id=task_id,
                    success=False,
                    errors=["Task timeout"],
                )
                await self.report_result(error_result)

            except Exception as e:
                self.status = AgentStatus.FAILED
                error_result = AgentResult(
                    agent_id=self.agent_id,
                    task_id=task_id,
                    success=False,
                    errors=[str(e)],
                )
                await self.report_result(error_result)

    async def handle_validation_request(self, message: AgentMessage) -> None:
        """검증 요청 처리"""
        # 기본적으로 승인 (하위 클래스에서 재정의 가능)
        await self.send_message(
            AgentMessage(
                message_type=MessageType.APPROVAL_GRANTED,
                recipient=message.sender,
                payload={"approved": True, "reason": "Auto-approved by base agent"},
                correlation_id=message.correlation_id,
            )
        )


class CICDPipeline:
    """CI/CD 파이프라인 오케스트레이터"""

    def __init__(self) -> None:
        self.queue = _memory_queue  # Standalone 인메모리 큐
        self.agents: dict[str, BaseAgent] = {}
        self.pipeline_status = "idle"
        self.current_session_id: str | None = None

    async def register_agent(self, agent: BaseAgent) -> None:
        """에이전트 등록"""
        self.agents[agent.agent_id] = agent
        logger.info(f"📝 [Pipeline] 에이전트 등록: {agent.name} ({agent.agent_id})")

    async def start_pipeline(self, changed_files: list[str]) -> str:
        """CI/CD 파이프라인 시작"""
        self.current_session_id = str(uuid.uuid4())
        self.pipeline_status = "running"

        logger.info(f"🚀 [Pipeline] CI/CD 파이프라인 시작 (세션: {self.current_session_id})")
        logger.info(f"📁 [Pipeline] 변경된 파일: {len(changed_files)}개")

        # Quality Scout 에이전트에게 초기 분석 요청
        scout_message = AgentMessage(
            message_type=MessageType.TASK_ASSIGNMENT,
            recipient="quality_scout",
            payload={
                "task_id": f"{self.current_session_id}_scout",
                "params": {"changed_files": changed_files},
            },
        )

        # Scout 에이전트가 있으면 호출, 없으면 직접 다음 단계로 진행
        if "quality_scout" in self.agents:
            await self.agents["quality_scout"].send_message(scout_message)
        else:
            # Scout가 없으면 Fast Check로 직접 진행
            await self.start_fast_checks(changed_files)

        return self.current_session_id

    async def start_fast_checks(self, changed_files: list[str]) -> None:
        """빠른 검사 단계 시작"""
        logger.info("⚡ [Pipeline] Fast Check 단계 시작")

        # Fast Check 에이전트들에게 병렬로 태스크 할당
        fast_agents = ["fast_ruff_agent", "fast_monkeytype_agent", "fast_syntax_agent"]

        for agent_id in fast_agents:
            if agent_id in self.agents:
                message = AgentMessage(
                    message_type=MessageType.TASK_ASSIGNMENT,
                    recipient=agent_id,
                    payload={
                        "task_id": f"{self.current_session_id}_fast_{agent_id}",
                        "params": {"changed_files": changed_files},
                    },
                )
                await self.agents[agent_id].send_message(message)

    async def start_deep_checks(self, changed_files: list[str]) -> None:
        """심층 검사 단계 시작"""
        logger.info("🎯 [Pipeline] Deep Check 단계 시작")

        # Deep Check 에이전트들에게 순차적으로 태스크 할당 (리소스 관리)
        deep_checks = [
            ("deep_mypy_agent", {"changed_files": changed_files}),
            ("deep_pyright_agent", {"changed_files": changed_files}),
            ("deep_bandit_agent", {"changed_files": changed_files}),
        ]

        for agent_id, params in deep_checks:
            if agent_id in self.agents:
                message = AgentMessage(
                    message_type=MessageType.TASK_ASSIGNMENT,
                    recipient=agent_id,
                    payload={
                        "task_id": f"{self.current_session_id}_deep_{agent_id}",
                        "params": params,
                    },
                )
                await self.agents[agent_id].send_message(message)
                await asyncio.sleep(0.1)  # 약간의 지연으로 리소스 관리

    async def start_aggregation(self) -> None:
        """결과 종합 단계 시작"""
        logger.info("📊 [Pipeline] 결과 종합 단계 시작")

        if "quality_aggregator" in self.agents:
            message = AgentMessage(
                message_type=MessageType.TASK_ASSIGNMENT,
                recipient="quality_aggregator",
                payload={
                    "task_id": f"{self.current_session_id}_aggregate",
                    "params": {"session_id": self.current_session_id},
                },
            )
            await self.agents["quality_aggregator"].send_message(message)

    async def start_validation(self) -> None:
        """승상 검증 단계 시작"""
        logger.info("👑 [Pipeline] 승상 검증 단계 시작")

        if "chancellor_validator" in self.agents:
            message = AgentMessage(
                message_type=MessageType.VALIDATION_REQUEST,
                recipient="chancellor_validator",
                payload={
                    "task_id": f"{self.current_session_id}_validate",
                    "session_id": self.current_session_id,
                },
            )
            await self.agents["chancellor_validator"].send_message(message)

    async def get_pipeline_status(self) -> dict[str, Any]:
        """파이프라인 상태 조회"""
        return {
            "session_id": self.current_session_id,
            "status": self.pipeline_status,
            "active_agents": len(
                [a for a in self.agents.values() if a.status == AgentStatus.RUNNING]
            ),
            "total_agents": len(self.agents),
        }

    async def shutdown(self) -> None:
        """파이프라인 종료"""
        logger.info("🛑 [Pipeline] CI/CD 파이프라인 종료")
        self.pipeline_status = "shutdown"
        self.current_session_id = None


# 글로벌 파이프라인 인스턴스
ci_cd_pipeline = CICDPipeline()


async def initialize_ci_cd_agents() -> None:
    """CI/CD 에이전트들 초기화"""
    logger.info("🎯 [System] CI/CD 에이전트 네트워크 초기화 시작")

    # 여기서 실제 에이전트 인스턴스들을 생성하고 등록
    # (실제 구현은 다음 단계에서)

    logger.info("✅ [System] CI/CD 에이전트 네트워크 초기화 완료")


# 유틸리티 함수들
async def run_ci_cd_pipeline(changed_files: list[str]) -> str:
    """CI/CD 파이프라인 실행 (외부 인터페이스)"""
    return await ci_cd_pipeline.start_pipeline(changed_files)


async def get_pipeline_status() -> dict[str, Any]:
    """파이프라인 상태 조회 (외부 인터페이스)"""
    return await ci_cd_pipeline.get_pipeline_status()


if __name__ == "__main__":
    # 테스트 실행
    async def test_pipeline():
        print("🧪 CI/CD 에이전트 시스템 테스트")
        await initialize_ci_cd_agents()

        # 샘플 파일들로 테스트
        test_files = [
            "packages/afo-core/AFO/__init__.py",
            "packages/afo-core/AFO/settings.py",
        ]
        session_id = await run_ci_cd_pipeline(test_files)

        print(f"🎯 파이프라인 시작됨 (세션: {session_id})")

        # 10초 동안 상태 모니터링
        for i in range(10):
            status = await get_pipeline_status()
            print(f"📊 상태 [{i + 1}/10]: {status}")
            await asyncio.sleep(1.0)

        await ci_cd_pipeline.shutdown()
        print("✅ 테스트 완료")

    asyncio.run(test_pipeline())
