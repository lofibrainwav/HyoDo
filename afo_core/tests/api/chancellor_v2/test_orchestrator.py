"""Tests for ChancellorOrchestrator and related components.

Orchestrator 패턴 적용 후 3 Strategists 병렬 실행 테스트.
"""

from __future__ import annotations

import pytest
from api.chancellor_v2.orchestrator import (
    ChancellorOrchestrator,
    ResultAggregator,
    StrategistContext,
    StrategistRegistry,
)
from api.chancellor_v2.sub_agents import (
    BaseStrategist,
    YiSunSinAgent,
    ShinSaimdangAgent,
    JangYeongSilAgent,
)


class TestStrategistContext:
    """StrategistContext 단위 테스트."""

    def test_create_context(self) -> None:
        """컨텍스트 생성 테스트."""
        ctx = StrategistContext(
            strategist_name="Jang Yeong-sil",
            pillar="TRUTH",
            command="test command",
            plan={"skill_id": "test_skill", "query": "test query"},
        )

        assert ctx.strategist_name == "Jang Yeong-sil"
        assert ctx.pillar == "TRUTH"
        assert ctx.skill_id == "test_skill"
        assert ctx.query == "test query"
        assert ctx.score == 0.0
        assert not ctx.has_errors

    def test_mark_completed(self) -> None:
        """완료 표시 테스트."""
        ctx = StrategistContext()
        ctx.mark_started()
        ctx.score = 0.85
        ctx.reasoning = "Test reasoning"
        ctx.mark_completed()

        # 시간이 같거나 이후일 수 있음 (매우 빠른 실행)
        assert ctx.completed_at >= ctx.started_at
        assert ctx.duration_ms >= 0

    def test_to_output_dict(self) -> None:
        """출력 딕셔너리 변환 테스트."""
        ctx = StrategistContext(
            strategist_name="Yi Sun-sin",
            pillar="GOODNESS",
        )
        ctx.score = 0.9
        ctx.reasoning = "Good"
        ctx.issues = ["minor issue"]
        ctx.mark_completed()

        output = ctx.to_output_dict()

        assert output["score"] == 0.9
        assert output["reasoning"] == "Good"
        assert len(output["issues"]) == 1
        assert "strategist" in output["metadata"]


class TestStrategistRegistry:
    """StrategistRegistry 단위 테스트."""

    def test_register_and_get(self) -> None:
        """등록 및 조회 테스트."""
        registry = StrategistRegistry()
        agent = JangYeongSilAgent()

        registry.register("truth", agent)

        assert registry.has("truth")
        assert registry.get("truth") is agent
        assert "truth" in registry

    def test_get_all_pillars(self) -> None:
        """전체 기둥 조회 테스트."""
        registry = StrategistRegistry()
        registry.register("truth", JangYeongSilAgent())
        registry.register("goodness", YiSunSinAgent())
        registry.register("beauty", ShinSaimdangAgent())

        pillars = registry.get_pillars()

        assert len(pillars) == 3
        assert "truth" in pillars
        assert "goodness" in pillars
        assert "beauty" in pillars


class TestStrategistAgents:
    """3 Strategists 에이전트 테스트."""

    def test_jang_yeong_sil_heuristic(self) -> None:
        """제갈량 휴리스틱 평가 테스트."""
        agent = JangYeongSilAgent()
        ctx = StrategistContext(
            plan={"skill_id": "pytest_runner", "query": "type check with mypy"},
        )

        score = agent.heuristic_evaluate(ctx)

        assert 0.0 <= score <= 1.0
        assert score >= 0.5  # 기본값 이상

    def test_yi_sun_sin_heuristic(self) -> None:
        """사마의 휴리스틱 평가 테스트."""
        agent = YiSunSinAgent()
        ctx = StrategistContext(
            plan={"skill_id": "security_scan", "query": "check authentication"},
        )

        score = agent.heuristic_evaluate(ctx)

        assert 0.0 <= score <= 1.0
        assert score >= 0.5

    def test_shin_saimdang_heuristic(self) -> None:
        """주유 휴리스틱 평가 테스트."""
        agent = ShinSaimdangAgent()
        ctx = StrategistContext(
            plan={"skill_id": "ui_component", "query": "clean minimal design"},
        )

        score = agent.heuristic_evaluate(ctx)

        assert 0.0 <= score <= 1.0
        assert score >= 0.5

    def test_agent_constants(self) -> None:
        """에이전트 상수 확인 테스트."""
        agents = [JangYeongSilAgent(), YiSunSinAgent(), ShinSaimdangAgent()]

        for agent in agents:
            assert agent.PILLAR in ["TRUTH", "GOODNESS", "BEAUTY"]
            assert agent.SCHOLAR_KEY != ""
            assert 0.0 < agent.WEIGHT <= 0.35
            assert agent.NAME_KO != ""
            assert agent.NAME_EN != ""


class TestResultAggregator:
    """ResultAggregator 단위 테스트."""

    def test_calculate_trinity_score(self) -> None:
        """Trinity Score 계산 테스트."""
        aggregator = ResultAggregator()

        # 모의 결과 생성
        results = {
            "truth": StrategistContext(score=0.9),
            "goodness": StrategistContext(score=0.85),
            "beauty": StrategistContext(score=0.8),
        }

        trinity_score, pillar_scores = aggregator.calculate_trinity_score(
            results, serenity_score=0.8, eternity_score=0.8
        )

        # Trinity = 0.35×0.9 + 0.35×0.85 + 0.20×0.8 + 0.08×0.8 + 0.02×0.8
        #         = 0.315 + 0.2975 + 0.16 + 0.064 + 0.016 = 0.8525
        assert 80 <= trinity_score <= 90
        assert pillar_scores["truth"] == 0.9
        assert pillar_scores["goodness"] == 0.85

    def test_calculate_risk_score(self) -> None:
        """Risk Score 계산 테스트."""
        aggregator = ResultAggregator()

        pillar_scores = {"goodness": 0.9}
        risk = aggregator.calculate_risk_score(pillar_scores)

        # Risk = (1.0 - 0.9) × 100 = 10
        assert risk == 10.0

    def test_make_decision_auto_run(self) -> None:
        """AUTO_RUN 판정 테스트."""
        aggregator = ResultAggregator()

        decision = aggregator.make_decision(
            trinity_score=92.0,
            risk_score=8.0,
            pillar_scores={"truth": 0.95, "goodness": 0.92, "beauty": 0.9},
        )

        assert decision["decision"] == "AUTO_RUN"

    def test_make_decision_ask_commander(self) -> None:
        """ASK_COMMANDER 판정 테스트."""
        aggregator = ResultAggregator()

        decision = aggregator.make_decision(
            trinity_score=80.0,
            risk_score=15.0,
            pillar_scores={"truth": 0.8, "goodness": 0.85, "beauty": 0.75},
        )

        assert decision["decision"] == "ASK_COMMANDER"

    def test_make_decision_block(self) -> None:
        """BLOCK 판정 테스트."""
        aggregator = ResultAggregator()

        decision = aggregator.make_decision(
            trinity_score=60.0,
            risk_score=40.0,
            pillar_scores={"truth": 0.6, "goodness": 0.6, "beauty": 0.5},
        )

        assert decision["decision"] == "BLOCK"


class TestChancellorOrchestrator:
    """ChancellorOrchestrator 통합 테스트."""

    def test_orchestrator_initialization(self) -> None:
        """Orchestrator 초기화 테스트."""
        orchestrator = ChancellorOrchestrator()

        assert len(orchestrator.registry) == 3
        assert orchestrator.registry.has("truth")
        assert orchestrator.registry.has("goodness")
        assert orchestrator.registry.has("beauty")

    def test_create_contexts(self) -> None:
        """컨텍스트 생성 테스트."""
        orchestrator = ChancellorOrchestrator()

        # Mock GraphState
        class MockState:
            input = {"command": "test"}
            plan = {"skill_id": "test", "query": "test"}

        contexts = orchestrator._create_contexts(MockState(), ["truth", "goodness"])

        assert len(contexts) == 2
        assert "truth" in contexts
        assert "goodness" in contexts
        assert contexts["truth"].pillar == "TRUTH"

    def test_get_full_assessment(self) -> None:
        """전체 평가 결과 테스트."""
        orchestrator = ChancellorOrchestrator()

        results = {
            "truth": StrategistContext(score=0.9, reasoning="Good"),
            "goodness": StrategistContext(score=0.85, reasoning="Safe"),
            "beauty": StrategistContext(score=0.8, reasoning="Clean"),
        }

        assessment = orchestrator.get_full_assessment(results)

        assert hasattr(assessment, "decision")
        assert hasattr(assessment, "trinity_score")
        assert hasattr(assessment, "risk_score")
        assert hasattr(assessment, "strategist_results")
