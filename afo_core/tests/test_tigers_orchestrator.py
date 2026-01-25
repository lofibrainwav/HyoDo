"""
통합 테스트 - 왕국 5호장군 혁명적 시스템 통합 검증

모든 구현된 컴포넌트에 대한 종합 테스트.
각 컴포넌트가 올바르게 통합되는지 검증합니다.
"""

import asyncio
from datetime import UTC, datetime
from typing import Any, Dict

import pytest
from tigers_orchestrator.circuit_breakers import (
    CircuitState,
    TigerCircuitBreaker,
)
from tigers_orchestrator.decision_engine import (
    TigerGeneralsAmbassador,
)
from tigers_orchestrator.event_bus import (
    MessageChannel,
    TigerGeneralsEventBus,
)
from tigers_orchestrator.message_protocol import (
    CrossPillarMessage,
    MessagePriority,
    MessageType,
)
from tigers_orchestrator.models import (
    BeautyCraftInput,
    BeautyCraftOutput,
    GoodnessGateInput,
    GoodnessGateOutput,
    TruthGuardInput,
    TruthGuardOutput,
)
from tigers_orchestrator.scoring import (
    TIGER_WEIGHTS,
    TrinityScoreAggregator,
)


class MockGeneral:
    """모의 5호장군"""

    def __init__(self, name: str) -> None:
        self.name = name
        self.call_count = 0
        self.success_count = 0

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """모의 실행"""
        self.call_count += 1

        if self.name == "truth_guard":
            return {"success": True, "score": 95.0, "output": "type_valid", "execution_time": 0.01}
        elif self.name == "goodness_gate":
            return {
                "success": True,
                "score": 90.0,
                "risk_score": 5.0,
                "risk_level": "low",
                "output": "gate_passed",
            }
        elif self.name == "beauty_craft":
            return {"success": True, "score": 85.0, "beauty_score": 92.0, "output": "code_enhanced"}
        elif self.name == "serenity_deploy":
            return {"success": True, "score": 88.0, "deployment_status": "ready"}
        elif self.name == "eternity_log":
            return {"success": True, "score": 100.0, "log_id": "log_001", "persisted": True}


class MockEventBus(TigerGeneralsEventBus):
    """테스트용 Event Bus"""

    def __init__(self) -> None:
        super().__init__()
        self.published_messages = []

    async def create_channel(self, general_name: str) -> MessageChannel:
        return await super().create_channel(general_name)

    async def publish(
        self,
        source: str,
        target: str | None,
        message_type: str,
        content: str,
        data: dict[str, Any] | None,
        priority: str = "MEDIUM",
    ) -> bool:
        result = await super().publish(
            source=source,
            target=target,
            message_type=message_type,
            content=content,
            data=data,
            priority=priority,
        )

        self.published_messages.append(
            {"source": source, "type": message_type, "content": content, "priority": priority}
        )

        return result

    def get_published_messages(self) -> list[dict[str, Any]]:
        """발행된 메시지 조회"""
        return self.published_messages.copy()


@pytest.fixture
async def event_bus():
    """Event Bus fixture"""
    bus = TigerGeneralsEventBus()

    for general in [
        "truth_guard",
        "goodness_gate",
        "beauty_craft",
        "serenity_deploy",
        "eternity_log",
    ]:
        await bus.create_channel(general)

    return bus


@pytest.fixture
async def scoring_aggregator():
    """Scoring aggregator fixture"""
    return TrinityScoreAggregator()


@pytest.fixture
async def ambassador(event_bus, scoring_aggregator):
    """Ambassador fixture"""
    return TigerGeneralsAmbassador(event_bus, scoring_aggregator)


class TestTigerGeneralsOrchestration:
    """5호장군 오케스트레이션 통합 테스트"""

    @pytest.mark.asyncio
    async def test_complete_workflow(self, event_bus, scoring_aggregator, ambassador):
        """완전 워크플로우 테스트"""

        # 1. Mock Generals 생성
        generals = {
            name: MockGeneral(name)
            for name in [
                "truth_guard",
                "goodness_gate",
                "beauty_craft",
                "serenity_deploy",
                "eternity_log",
            ]
        }

        # 2. 모든 General 실행
        results = {}
        for name, general in generals.items():
            result = await general.execute({})
            results[name] = result

        # 3. 점수 집계
        for name, result in results.items():
            if "score" in result:
                scoring_aggregator.add_score(name, result["score"])

        # 4. Trinity Score 계산
        trinity_score = scoring_aggregator.calculate_trinity_score()
        risk_score = scoring_aggregator.calculate_risk_score(
            {"test_results": {"total": 100, "failed": 5}}
        )
        decision = scoring_aggregator.get_decision()

        # 5. Ambassador로 결정 실행
        ambassador_result = await ambassador.execute_auto_run(
            {
                "trinity_score": trinity_score,
                "risk_score": risk_score,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

        # 6. 검증
        assert decision in ["AUTO_RUN", "ASK_COMMANDER", "BLOCK"]
        assert trinity_score >= 70.0
        assert trinity_score <= 100.0
        assert risk_score >= 0.0
        assert risk_score <= 100.0
        assert ambassador_result is not None

    @pytest.mark.asyncio
    async def test_event_bus_messaging(self, event_bus):
        """Event Bus 메시징 테스트"""

        # 메시지 발행
        result = await event_bus.publish(
            source="truth_guard",
            target="goodness_gate",
            message_type="insight",
            content="Truth validation passed",
            data={"test_key": "test_value"},
            priority="HIGH",
        )

        # 발행 성공 확인
        assert result is True

        # Event Log 확인
        assert len(event_bus.event_log) == 1
        assert event_bus.event_log[0]["source"] == "truth_guard"
        assert event_bus.event_log[0]["type"] == "insight"
        assert event_bus.event_log[0]["content"] == "Truth validation passed"

    @pytest.mark.asyncio
    async def test_scoring_aggregation(self, scoring_aggregator):
        """점수 집계 테스트"""

        # 개별 점수 추가
        scoring_aggregator.add_score("truth_guard", 95.0)
        scoring_aggregator.add_score("goodness_gate", 90.0)
        scoring_aggregator.add_score("beauty_craft", 85.0)
        scoring_aggregator.add_score("serenity_deploy", 88.0)
        scoring_aggregator.add_score("eternity_log", 100.0)

        # Trinity Score 계산
        trinity_score = scoring_aggregator.calculate_trinity_score()

        # 가중치 검증 (예상: 95*0.35 + 90*0.35 + 85*0.20 + 88*0.05 + 100*0.05 = 91.15)
        assert abs(trinity_score - 91.15) < 0.1

    @pytest.mark.asyncio
    async def test_decision_matrix(self, scoring_aggregator):
        """Decision Matrix 테스트"""

        # AUTO_RUN 조건: Trinity >= 90 and Risk <= 10
        scoring_aggregator.add_score("truth_guard", 95.0)
        scoring_aggregator.add_score("goodness_gate", 95.0)
        scoring_aggregator.add_score("beauty_craft", 90.0)
        scoring_aggregator.add_score("serenity_deploy", 90.0)
        scoring_aggregator.add_score("eternity_log", 90.0)
        # Trinity: 95*0.35 + 95*0.35 + 90*0.20 + 90*0.05 + 90*0.05 = 93.5

        decision = scoring_aggregator.get_decision()
        assert decision == "AUTO_RUN"

        # ASK_COMMANDER 조건: 70 <= Trinity < 90 and Risk <= 10
        scoring_aggregator2 = TrinityScoreAggregator()
        scoring_aggregator2.add_score("truth_guard", 80.0)
        scoring_aggregator2.add_score("goodness_gate", 80.0)
        scoring_aggregator2.add_score("beauty_craft", 75.0)
        scoring_aggregator2.add_score("serenity_deploy", 75.0)
        scoring_aggregator2.add_score("eternity_log", 75.0)
        # Trinity: 80*0.35 + 80*0.35 + 75*0.20 + 75*0.05 + 75*0.05 = 78.5

        decision = scoring_aggregator2.get_decision()
        assert decision == "ASK_COMMANDER"

        # BLOCK 조건: Trinity < 70 or Risk > 10
        scoring_aggregator3 = TrinityScoreAggregator()
        scoring_aggregator3.add_score("truth_guard", 60.0)
        scoring_aggregator3.add_score("goodness_gate", 60.0)
        scoring_aggregator3.add_score("beauty_craft", 60.0)
        scoring_aggregator3.add_score("serenity_deploy", 60.0)
        scoring_aggregator3.add_score("eternity_log", 60.0)
        # Trinity: 60*1.0 = 60.0

        decision = scoring_aggregator3.get_decision()
        assert decision == "BLOCK"

    @pytest.mark.asyncio
    async def test_integration_all_components(self, event_bus, scoring_aggregator, ambassador):
        """전체 통합 테스트"""

        # 1. 모든 채널 생성
        for general in [
            "truth_guard",
            "goodness_gate",
            "beauty_craft",
            "serenity_deploy",
            "eternity_log",
        ]:
            await event_bus.create_channel(general)

        # 2. 메시지 발행
        await event_bus.publish(
            source="test",
            target="ALL",
            message_type="insight",
            content="Integration test started",
            data={"test": "integration"},
            priority="MEDIUM",
        )

        # 3. 점수 집계 (모든 general의 점수 추가)
        for name, score in [
            ("truth_guard", 95.0),
            ("goodness_gate", 95.0),
            ("beauty_craft", 90.0),
            ("serenity_deploy", 90.0),
            ("eternity_log", 90.0),
        ]:
            scoring_aggregator.add_score(name, score)

        # 4. Trinity Score 확인
        trinity_score = scoring_aggregator.calculate_trinity_score()
        risk_score = scoring_aggregator.calculate_risk_score(
            {"test_results": {"total": 100, "failed": 0}}
        )
        decision = scoring_aggregator.get_decision()

        # 5. Ambassador 실행
        result = await ambassador.execute_auto_run(
            {
                "trinity_score": trinity_score,
                "risk_score": risk_score,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

        # 6. 전체 검증
        assert decision == "AUTO_RUN"
        assert result is not None
        assert len(event_bus.event_log) >= 1
