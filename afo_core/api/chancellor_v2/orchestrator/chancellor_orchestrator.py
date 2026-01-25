# Trinity Score: 95.0 (眞 - Technical Excellence)
"""Chancellor Orchestrator V3 - 단일 진입점 Orchestrator.

3 Strategists를 독립 컨텍스트에서 병렬 실행하고,
결과를 수집하여 Trinity Score 및 DecisionResult를 생성합니다.

V3 개선사항:
- CostAwareRouter: 작업 복잡도 기반 모델 선택 (비용 40% 절감)
- KeyTriggerRouter: 키워드 기반 Strategist 선택 (불필요 평가 30% 감소)

세종대왕의 정신 (King Sejong's Spirit):
- 眞 (Truth): 장영실 - 측우기, 자격루의 정밀함
- 善 (Goodness): 이순신 - 거북선, 학익진의 수호
- 美 (Beauty): 신사임당 - 초충도, 묵죽도의 예술혼
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from .cost_aware_router import CostAwareRouter, get_cost_aware_router
from .key_trigger_router import KeyTriggerRouter, get_key_trigger_router
from .models import AssessmentResult, RoutingInfo
from .result_aggregator import ResultAggregator
from .strategist_context import StrategistContext
from .sub_agent_registry import StrategistRegistry

if TYPE_CHECKING:
    from ..graph.state import GraphState
    from ..sub_agents.base_strategist import BaseStrategist

logger = logging.getLogger(__name__)


# Strategist 이름 매핑 - 세종대왕의 정신 (King Sejong's Spirit)
STRATEGIST_NAMES = {
    "truth": "장영실 (Jang Yeong-sil)",  # 眞 - 측우기, 자격루의 정밀함
    "goodness": "이순신 (Yi Sun-sin)",  # 善 - 거북선, 학익진의 수호
    "beauty": "신사임당 (Shin Saimdang)",  # 美 - 초충도, 묵죽도의 예술혼
}


class ChancellorOrchestrator:
    """Chancellor Graph V3 Orchestrator.

    단일 진입점으로 3 Strategists를 독립 컨텍스트에서 병렬 실행하고,
    결과를 수집하여 Trinity Score 및 DecisionResult를 생성합니다.

    V3 Features:
        - CostAwareRouter: 작업 복잡도 기반 최적 모델 선택
        - KeyTriggerRouter: 키워드 기반 필요 Strategist만 선택

    Usage:
        orchestrator = ChancellorOrchestrator()
        results = await orchestrator.orchestrate_assessment(state)
        state = orchestrator.aggregate_to_state(state, results)

        # V3: 스마트 라우팅 사용
        results = await orchestrator.orchestrate_assessment(state, use_smart_routing=True)
    """

    def __init__(
        self,
        cost_router: CostAwareRouter | None = None,
        key_trigger_router: KeyTriggerRouter | None = None,
    ) -> None:
        """Orchestrator 초기화.

        Args:
            cost_router: 비용 인식 라우터 (None이면 싱글톤 사용)
            key_trigger_router: 키워드 트리거 라우터 (None이면 싱글톤 사용)
        """
        self.registry = StrategistRegistry()
        self.aggregator = ResultAggregator()
        self.cost_router = cost_router or get_cost_aware_router()
        self.key_trigger_router = key_trigger_router or get_key_trigger_router()
        self._register_default_strategists()

    def _register_default_strategists(self) -> None:
        """기본 3 Strategists 등록 - 세종대왕의 정신."""
        from ..sub_agents.jang_yeong_sil_agent import JangYeongSilAgent
        from ..sub_agents.shin_saimdang_agent import ShinSaimdangAgent
        from ..sub_agents.yi_sun_sin_agent import YiSunSinAgent

        self.registry.register("truth", JangYeongSilAgent())
        self.registry.register("goodness", YiSunSinAgent())
        self.registry.register("beauty", ShinSaimdangAgent())

        logger.debug(
            f"Registered {len(self.registry)} strategists: {', '.join(self.registry.get_pillars())}"
        )

    async def orchestrate_assessment(
        self,
        state: GraphState,
        include_pillars: list[str] | None = None,
        use_smart_routing: bool = True,
    ) -> dict[str, StrategistContext]:
        """3 Strategists 병렬 평가 오케스트레이션.

        Args:
            state: 현재 그래프 상태
            include_pillars: 평가할 기둥 목록 (None이면 스마트 라우팅 또는 전체)
            use_smart_routing: True면 KeyTriggerRouter로 자동 선택

        Returns:
            각 Strategist별 완료된 컨텍스트
        """
        command = state.input.get("command", "")

        # V3: 스마트 라우팅으로 필요한 Pillar만 선택
        if include_pillars:
            pillars = include_pillars
        elif use_smart_routing and command:
            analysis = self.key_trigger_router.analyze_command(command)
            pillars = analysis.pillars
            logger.info(
                f"[V3] KeyTriggerRouter selected pillars: {pillars} "
                f"(confidence: {analysis.confidence:.2f}, "
                f"triggers: {analysis.total_triggers_matched})"
            )
        else:
            pillars = ["truth", "goodness", "beauty"]

        # V3: 비용 인식 라우팅 정보 로깅
        if command:
            cost_info = self.cost_router.estimate_cost(command, state.plan)
            logger.info(
                f"[V3] CostAwareRouter: tier={cost_info.tier}, "
                f"model={cost_info.model}, "
                f"est_cost=${cost_info.estimated_cost_usd:.6f}"
            )
            # Plan에 비용 정보 추가
            state.plan["_cost_tier"] = cost_info.tier
            state.plan["_cost_model"] = cost_info.model

        logger.info(f"Starting orchestration for pillars: {pillars}")

        # 1. 각 Strategist용 독립 컨텍스트 생성
        contexts = self._create_contexts(state, pillars)

        # 2. 병렬 실행 태스크 생성
        tasks = []
        task_pillars = []
        for pillar, ctx in contexts.items():
            strategist = self.registry.get(pillar)
            if strategist:
                tasks.append(self._execute_strategist(strategist, ctx))
                task_pillars.append(pillar)
            else:
                logger.warning(f"No strategist registered for pillar: {pillar}")

        # 3. 병렬 실행
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # 4. 결과 매핑
        completed: dict[str, StrategistContext] = {}
        for i, result in enumerate(results_list):
            pillar = task_pillars[i]
            if isinstance(result, StrategistContext):
                completed[pillar] = result
                logger.debug(
                    f"Strategist {pillar} completed: "
                    f"score={result.score:.3f}, "
                    f"duration={result.duration_ms:.1f}ms"
                )
            elif isinstance(result, Exception):
                logger.error(f"Strategist {pillar} failed with exception: {result}")
                # 실패한 경우 빈 컨텍스트로 대체
                fallback_ctx = contexts[pillar]
                fallback_ctx.score = 0.5
                fallback_ctx.reasoning = f"Execution failed: {result}"
                fallback_ctx.errors.append(str(result))
                fallback_ctx.mark_completed()
                completed[pillar] = fallback_ctx

        logger.info(f"Orchestration completed: {len(completed)}/{len(pillars)} strategists")

        return completed

    async def _execute_strategist(
        self,
        strategist: BaseStrategist,
        ctx: StrategistContext,
    ) -> StrategistContext:
        """단일 Strategist 안전 실행.

        Args:
            strategist: Strategist 인스턴스
            ctx: 실행 컨텍스트

        Returns:
            완료된 컨텍스트
        """
        try:
            return await strategist.evaluate(ctx)
        except Exception as e:
            logger.error(f"{strategist.PILLAR} evaluation error: {e}")
            ctx.errors.append(f"{strategist.display_name} evaluation failed: {e}")
            ctx.score = strategist.heuristic_evaluate(ctx)
            ctx.reasoning = f"Fallback to heuristic due to error: {e}"
            ctx.mark_completed()
            return ctx

    def _create_contexts(
        self,
        state: GraphState,
        pillars: list[str],
    ) -> dict[str, StrategistContext]:
        """상태로부터 독립 컨텍스트 생성.

        Args:
            state: GraphState 인스턴스
            pillars: 기둥 목록

        Returns:
            pillar -> StrategistContext 매핑
        """
        contexts = {}
        for pillar in pillars:
            contexts[pillar] = StrategistContext.from_graph_state(
                state,
                strategist_name=STRATEGIST_NAMES.get(pillar, "Unknown"),
                pillar=pillar.upper(),
            )
        return contexts

    def aggregate_to_state(
        self,
        state: GraphState,
        results: dict[str, StrategistContext],
    ) -> GraphState:
        """결과를 GraphState로 병합.

        Args:
            state: 원본 GraphState
            results: Strategist 결과

        Returns:
            업데이트된 GraphState
        """
        for pillar, ctx in results.items():
            state.outputs[pillar.upper()] = ctx.to_output_dict()
            state.errors.extend(ctx.errors)

        logger.debug(f"Aggregated {len(results)} strategist results to state")
        return state

    def get_full_assessment(
        self,
        results: dict[str, StrategistContext],
        serenity_score: float = 0.8,
        eternity_score: float = 0.8,
    ) -> AssessmentResult:
        """전체 평가 결과 (Trinity Score 포함).

        Args:
            results: Strategist 결과
            serenity_score: 孝 점수 (SERENITY 노드에서 제공)
            eternity_score: 永 점수 (ETERNITY 노드에서 제공)

        Returns:
            통합된 평가 결과 모델
        """
        return self.aggregator.aggregate_results(results, serenity_score, eternity_score)

    def get_routing_info(self, command: str, plan: dict[str, Any] | None = None) -> RoutingInfo:
        """V3 라우팅 정보 조회 (디버깅/모니터링용).

        Args:
            command: 사용자 명령어
            plan: 실행 계획

        Returns:
            라우팅 분석 결과
        """
        plan = plan or {}
        key_analysis = self.key_trigger_router.analyze_command(command)
        cost_info = self.cost_router.estimate_cost(command, plan)

        return RoutingInfo(
            version="V3",
            key_trigger=key_analysis,
            cost_aware=cost_info,
            optimization={
                "pillars_reduced": 3 - len(key_analysis.pillars),
                "estimated_savings_percent": round((1 - len(key_analysis.pillars) / 3) * 100, 1),
            },
        )


# 싱글톤 인스턴스 (선택적 사용)
_orchestrator: ChancellorOrchestrator | None = None


def get_orchestrator() -> ChancellorOrchestrator:
    """Orchestrator 싱글톤 인스턴스 반환."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ChancellorOrchestrator()
    return _orchestrator
