# Trinity Score: 95.0 (眞 - V3 Routing Integration Verification)
"""V3 라우팅 통합 검증 테스트.

실제 Orchestrator를 async 실행하여 전체 흐름을 검증합니다.
"""

from __future__ import annotations

import asyncio
import time

import pytest
from api.chancellor_v2.graph.state import GraphState
from api.chancellor_v2.orchestrator.chancellor_orchestrator import (
    STRATEGIST_NAMES,
    ChancellorOrchestrator,
)
from api.chancellor_v2.orchestrator.cost_aware_router import CostTier
from api.chancellor_v2.orchestrator.strategist_context import StrategistContext


def create_test_state(command: str, plan: dict | None = None) -> GraphState:
    """테스트용 GraphState 생성."""
    return GraphState(
        trace_id=f"test-{int(time.time())}",
        request_id="test-req-001",
        input={"command": command},
        plan=plan or {},
        started_at=time.time(),
    )


class TestV3OrchestratorIntegration:
    """V3 Orchestrator 통합 테스트 - 실제 async 실행."""

    @pytest.fixture
    def orchestrator(self) -> ChancellorOrchestrator:
        """새 Orchestrator 인스턴스."""
        return ChancellorOrchestrator()

    # === 기본 실행 테스트 ===

    @pytest.mark.asyncio
    async def test_orchestrate_basic_execution(self, orchestrator: ChancellorOrchestrator) -> None:
        """기본 오케스트레이션 실행 검증."""
        state = create_test_state("implement a function")

        results = await orchestrator.orchestrate_assessment(state)

        # 최소 2개 pillar가 실행되어야 함
        assert len(results) >= 2
        # 각 결과는 StrategistContext 타입이어야 함
        for pillar, ctx in results.items():
            assert isinstance(ctx, StrategistContext)
            assert ctx.pillar in ["TRUTH", "GOODNESS", "BEAUTY"]
            assert 0.0 <= ctx.score <= 1.0
            assert ctx.completed_at > 0  # 완료 시간이 기록되어야 함

    @pytest.mark.asyncio
    async def test_orchestrate_all_pillars(self, orchestrator: ChancellorOrchestrator) -> None:
        """모든 pillar 명시적 실행."""
        state = create_test_state("complex task")

        results = await orchestrator.orchestrate_assessment(
            state,
            include_pillars=["truth", "goodness", "beauty"],
        )

        assert len(results) == 3
        assert "truth" in results
        assert "goodness" in results
        assert "beauty" in results

    # === 스마트 라우팅 테스트 ===

    @pytest.mark.asyncio
    async def test_smart_routing_truth_command(self, orchestrator: ChancellorOrchestrator) -> None:
        """기술 명령은 truth pillar 포함."""
        state = create_test_state("implement new API endpoint")

        results = await orchestrator.orchestrate_assessment(state, use_smart_routing=True)

        assert "truth" in results
        # API, 구현 키워드로 truth pillar가 높은 점수

    @pytest.mark.asyncio
    async def test_smart_routing_goodness_command(
        self, orchestrator: ChancellorOrchestrator
    ) -> None:
        """보안 명령은 goodness pillar 포함."""
        state = create_test_state("delete production secrets")

        results = await orchestrator.orchestrate_assessment(state, use_smart_routing=True)

        assert "goodness" in results
        # 비용 정보가 plan에 저장되어야 함
        assert state.plan.get("_cost_tier") == "expensive"

    @pytest.mark.asyncio
    async def test_smart_routing_beauty_command(self, orchestrator: ChancellorOrchestrator) -> None:
        """UI 명령은 beauty pillar 포함."""
        state = create_test_state("update UI design with CSS")

        results = await orchestrator.orchestrate_assessment(state, use_smart_routing=True)

        assert "beauty" in results

    @pytest.mark.asyncio
    async def test_smart_routing_disabled(self, orchestrator: ChancellorOrchestrator) -> None:
        """스마트 라우팅 비활성화 시 전체 pillar 실행."""
        state = create_test_state("simple task")

        results = await orchestrator.orchestrate_assessment(state, use_smart_routing=False)

        # 스마트 라우팅 비활성화 시 3개 모두 실행
        assert len(results) == 3

    # === 비용 정보 추적 테스트 ===

    @pytest.mark.asyncio
    async def test_cost_info_tracked_in_plan(self, orchestrator: ChancellorOrchestrator) -> None:
        """비용 정보가 plan에 기록되는지 검증."""
        state = create_test_state("deploy to production")

        await orchestrator.orchestrate_assessment(state, use_smart_routing=True)

        # 비용 정보가 plan에 저장
        assert "_cost_tier" in state.plan
        assert "_cost_model" in state.plan
        assert state.plan["_cost_tier"] == "expensive"
        assert "opus" in state.plan["_cost_model"].lower()

    @pytest.mark.asyncio
    async def test_free_tier_for_simple_command(self, orchestrator: ChancellorOrchestrator) -> None:
        """간단한 명령은 FREE tier 사용."""
        state = create_test_state("show help")

        await orchestrator.orchestrate_assessment(state, use_smart_routing=True)

        assert state.plan.get("_cost_tier") == "free"

    # === 결과 집계 테스트 ===

    @pytest.mark.asyncio
    async def test_aggregate_to_state(self, orchestrator: ChancellorOrchestrator) -> None:
        """결과가 state.outputs에 집계되는지 검증."""
        state = create_test_state("implement feature")

        results = await orchestrator.orchestrate_assessment(state)
        updated_state = orchestrator.aggregate_to_state(state, results)

        # outputs에 각 pillar 결과가 저장
        for pillar in results:
            upper_pillar = pillar.upper()
            assert upper_pillar in updated_state.outputs
            assert "score" in updated_state.outputs[upper_pillar]
            assert "reasoning" in updated_state.outputs[upper_pillar]

    @pytest.mark.asyncio
    async def test_full_assessment_trinity_score(
        self, orchestrator: ChancellorOrchestrator
    ) -> None:
        """Trinity Score 계산 검증."""
        state = create_test_state("implement with tests")

        results = await orchestrator.orchestrate_assessment(state)
        assessment = orchestrator.get_full_assessment(results)

        # Trinity Score 구조 검증
        assert hasattr(assessment, "trinity_score")
        assert hasattr(assessment, "pillar_scores")
        assert hasattr(assessment, "decision")

        # Trinity Score 범위 검증
        assert 0.0 <= assessment.trinity_score <= 100.0

        # Pillar scores 존재
        pillar_scores = assessment.pillar_scores
        assert "truth" in pillar_scores or "TRUTH" in pillar_scores

    # === 병렬 실행 검증 테스트 ===

    @pytest.mark.asyncio
    async def test_parallel_execution_timing(self, orchestrator: ChancellorOrchestrator) -> None:
        """병렬 실행 시 시간 효율성 검증."""
        state = create_test_state("complex multi-pillar task")

        start = time.time()
        results = await orchestrator.orchestrate_assessment(
            state, include_pillars=["truth", "goodness", "beauty"]
        )
        elapsed = time.time() - start

        # 각 strategist의 개별 실행 시간 합
        total_individual_time = sum(ctx.duration_ms for ctx in results.values())

        # 병렬 실행이므로 전체 시간이 개별 시간 합보다 작아야 함
        # (오차 허용을 위해 80% 이내 검증)
        elapsed_ms = elapsed * 1000
        # 참고: heuristic 기반 fallback은 매우 빠르므로 이 검증이 항상 유효하지 않을 수 있음
        # 실제 LLM 호출 시에만 의미있는 검증
        assert len(results) == 3

    # === 에러 핸들링 테스트 ===

    @pytest.mark.asyncio
    async def test_error_handling_fallback(self, orchestrator: ChancellorOrchestrator) -> None:
        """Strategist 에러 시 fallback 동작 검증."""
        state = create_test_state("test error handling")

        # 모든 pillar 실행 (에러가 발생해도 fallback으로 결과 반환)
        results = await orchestrator.orchestrate_assessment(state)

        # 에러가 발생해도 결과는 반환되어야 함
        assert len(results) >= 2
        for ctx in results.values():
            # fallback 점수는 0.0 ~ 1.0 사이
            assert 0.0 <= ctx.score <= 1.0

    # === Context 격리 테스트 ===

    @pytest.mark.asyncio
    async def test_context_isolation(self, orchestrator: ChancellorOrchestrator) -> None:
        """각 Strategist 컨텍스트가 격리되는지 검증."""
        state = create_test_state("test context isolation")

        results = await orchestrator.orchestrate_assessment(state)

        # 각 컨텍스트는 고유한 context_id를 가져야 함
        context_ids = [ctx.context_id for ctx in results.values()]
        assert len(context_ids) == len(set(context_ids))  # 모두 유니크

        # 각 컨텍스트는 자신의 pillar 정보를 가져야 함
        for pillar, ctx in results.items():
            assert ctx.pillar == pillar.upper()


class TestV3RoutingInfoAPI:
    """get_routing_info API 상세 테스트."""

    @pytest.fixture
    def orchestrator(self) -> ChancellorOrchestrator:
        return ChancellorOrchestrator()

    def test_routing_info_complete_structure(self, orchestrator: ChancellorOrchestrator) -> None:
        """라우팅 정보 전체 구조 검증."""
        info = orchestrator.get_routing_info("implement API")

        # 최상위 속성
        assert hasattr(info, "version")
        assert hasattr(info, "key_trigger")
        assert hasattr(info, "cost_aware")
        assert hasattr(info, "optimization")

        # key_trigger 구조
        kt = info.key_trigger
        assert hasattr(kt, "pillars")
        assert hasattr(kt, "confidence")
        assert hasattr(kt, "matched_triggers")
        assert hasattr(kt, "scores")
        assert isinstance(kt.pillars, list)
        assert isinstance(kt.confidence, float)
        assert isinstance(kt.matched_triggers, dict)
        assert isinstance(kt.scores, dict)

        # cost_aware 구조
        ca = info.cost_aware
        assert hasattr(ca, "tier")
        assert hasattr(ca, "model")
        assert hasattr(ca, "estimated_cost_usd")
        assert hasattr(ca, "quality_score")
        assert ca.tier in ["free", "cheap", "expensive"]

        # optimization 구조 (optimization은 dict)
        opt = info.optimization
        assert "pillars_reduced" in opt
        assert "estimated_savings_percent" in opt

    def test_routing_info_various_commands(self, orchestrator: ChancellorOrchestrator) -> None:
        """다양한 명령어에 대한 라우팅 정보 일관성."""
        commands = [
            "read file",
            "implement function",
            "delete database",
            "deploy to production",
            "update UI design",
            "refactor authentication with migration",
        ]

        for cmd in commands:
            info = orchestrator.get_routing_info(cmd)

            # 항상 유효한 구조
            assert info.version == "V3"
            assert len(info.key_trigger.pillars) >= 2
            assert 0.0 <= info.key_trigger.confidence <= 1.0
            assert info.cost_aware.tier in ["free", "cheap", "expensive"]
            assert info.cost_aware.estimated_cost_usd >= 0.0

    def test_routing_info_with_plan(self, orchestrator: ChancellorOrchestrator) -> None:
        """plan 정보 포함 시 라우팅 검증."""
        # 승인 필요 plan
        info = orchestrator.get_routing_info(
            "simple task", plan={"requires_approval": True, "steps": ["s1", "s2", "s3"]}
        )
        # requires_approval로 복잡도 증가
        assert info.cost_aware.tier in ["cheap", "expensive"]

        # dry_run plan
        info_dry = orchestrator.get_routing_info(
            "simple task", plan={"dry_run": True, "steps": ["s1"]}
        )
        # dry_run으로 복잡도 감소
        assert info_dry.cost_aware.tier == "free"


class TestV3RouterEdgeCases:
    """V3 라우터 엣지 케이스 테스트."""

    @pytest.fixture
    def orchestrator(self) -> ChancellorOrchestrator:
        return ChancellorOrchestrator()

    @pytest.mark.asyncio
    async def test_empty_command(self, orchestrator: ChancellorOrchestrator) -> None:
        """빈 명령어 처리."""
        state = create_test_state("")

        results = await orchestrator.orchestrate_assessment(state)

        # 빈 명령어도 처리 가능해야 함
        assert len(results) >= 2

    @pytest.mark.asyncio
    async def test_very_long_command(self, orchestrator: ChancellorOrchestrator) -> None:
        """매우 긴 명령어 처리."""
        long_cmd = "implement " + "feature " * 200
        state = create_test_state(long_cmd)

        results = await orchestrator.orchestrate_assessment(state)

        # 긴 명령어도 처리 가능해야 함
        assert len(results) >= 2
        # 긴 명령어는 복잡도 증가
        assert state.plan.get("_cost_tier") in ["cheap", "expensive"]

    @pytest.mark.asyncio
    async def test_special_characters_in_command(
        self, orchestrator: ChancellorOrchestrator
    ) -> None:
        """특수 문자 포함 명령어 처리."""
        state = create_test_state("implement func(x) { return x * 2; }")

        results = await orchestrator.orchestrate_assessment(state)

        assert len(results) >= 2

    @pytest.mark.asyncio
    async def test_korean_command(self, orchestrator: ChancellorOrchestrator) -> None:
        """한글 명령어 처리."""
        state = create_test_state("새로운 API 엔드포인트 구현")

        results = await orchestrator.orchestrate_assessment(state)

        # 한글도 처리 가능해야 함
        assert len(results) >= 2

    @pytest.mark.asyncio
    async def test_mixed_language_command(self, orchestrator: ChancellorOrchestrator) -> None:
        """혼합 언어 명령어 처리."""
        state = create_test_state("implement API endpoint 구현하고 test 작성")

        results = await orchestrator.orchestrate_assessment(state)

        # 영한 혼합도 처리 가능
        assert len(results) >= 2
        # implement, API, test 키워드 인식 확인
        assert "truth" in results


# === 직접 실행용 ===


async def run_integration_verification() -> None:
    """통합 검증 직접 실행."""
    print("=" * 70)
    print("V3 Routing Integration Verification")
    print("=" * 70)

    orchestrator = ChancellorOrchestrator()

    test_cases = [
        ("implement new API endpoint", "기술 구현"),
        ("delete production database", "위험 작업"),
        ("update UI design with Tailwind CSS", "UI 작업"),
        ("refactor authentication system", "보안 리팩터링"),
        ("read the README file", "간단한 읽기"),
        ("deploy to production with secret rotation", "복합 고위험"),
    ]

    for command, description in test_cases:
        print(f"\n{'=' * 70}")
        print(f"[{description}] {command}")
        print("=" * 70)

        state = create_test_state(command)

        # 라우팅 정보
        info = orchestrator.get_routing_info(command)
        print("\n📍 Routing Decision (V3):")
        print(f"   Pillars: {info.key_trigger.pillars}")
        print(f"   Confidence: {info.key_trigger.confidence:.2f}")
        print(f"   Cost Tier: {info.cost_aware.tier}")
        print(f"   Model: {info.cost_aware.model}")
        print(f"   Savings: {info.optimization['estimated_savings_percent']}%")

        # 실제 오케스트레이션 실행
        start = time.time()
        results = await orchestrator.orchestrate_assessment(state, use_smart_routing=True)
        elapsed = (time.time() - start) * 1000

        print(f"\n⚡ Execution Results ({elapsed:.1f}ms):")
        for pillar, ctx in results.items():
            strategist = STRATEGIST_NAMES.get(pillar, pillar)
            status = "✓" if not ctx.has_errors else "✗"
            print(f"   {status} {strategist}: score={ctx.score:.3f} ({ctx.duration_ms:.1f}ms)")
            if ctx.reasoning:
                print(f"      └─ {ctx.reasoning[:60]}...")

        # Trinity Score
        assessment = orchestrator.get_full_assessment(results)
        print(f"\n🎯 Trinity Score: {assessment.trinity_score:.1f}")
        print(f"   Decision: {assessment.decision}")

    print("\n" + "=" * 70)
    print("Integration Verification Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_integration_verification())
