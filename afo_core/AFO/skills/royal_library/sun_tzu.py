"""제1서: 손자병법 (12선) - 眞 70% / 孝 30%

Rule #0 지피지기: "眞 100% 확보 후 행동" - 야전교범 제1원칙
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, TypeVar

from AFO.skills.royal_library.models import Classic, PrincipleResult

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)
T = TypeVar("T")

# Trinity 가중치
TRINITY_IMPACT = {"眞": 0.70, "孝": 0.30}


class SunTzuPrinciples:
    """손자병법 12선 원칙"""

    async def principle_01_preflight_check(
        self, context: dict[str, Any] | None = None, sources: list[str] | None = None
    ) -> PrincipleResult:
        """[01] 지피지기 (Know Thyself) - Rule #0

        원칙: 모든 실행 전, Context7과 DB를 조회하여 현재 상태를 정확히 파악하라.
        """
        sources = sources or []
        context = context or {}
        sources_verified = len(sources) >= 2
        context_loaded = bool(context)
        success = sources_verified or context_loaded

        return PrincipleResult(
            principle_id=1,
            principle_name="지피지기",
            classic=Classic.SUN_TZU,
            success=success,
            message=("眞 100% 확보 완료" if success else "출처 2개 이상 필요 (Rule #0 위반)"),
            data={
                "sources_count": len(sources),
                "context_loaded": context_loaded,
                "sources_verified": sources_verified,
            },
            trinity_impact=TRINITY_IMPACT,
        )

    async def principle_02_find_existing_solution(
        self, requirement: str, search_sources: list[str] | None = None
    ) -> PrincipleResult:
        """[02] 상병벌모 (Win Without Fighting)

        원칙: 코드를 짜는 것보다 기존 라이브러리/API를 활용하는 것이 상책이다.
        """
        search_sources = search_sources or ["pypi", "npm", "github"]
        return PrincipleResult(
            principle_id=2,
            principle_name="상병벌모",
            classic=Classic.SUN_TZU,
            success=True,
            message=f"기존 솔루션 검색 권장: {search_sources}",
            data={"requirement": requirement, "sources": search_sources},
            trinity_impact=TRINITY_IMPACT,
        )

    async def principle_03_dry_run_simulation(
        self, action: Callable[..., T], *args: Any, simulate: bool = True, **kwargs: Any
    ) -> PrincipleResult:
        """[03] 병자궤도야 (All Warfare is Deception) - DRY_RUN

        원칙: 위험한 작업은 반드시 DRY_RUN (모의전)으로 결과를 미리 보여주어라.
        """
        if simulate:
            return PrincipleResult(
                principle_id=3,
                principle_name="병자궤도야",
                classic=Classic.SUN_TZU,
                success=True,
                message="[DRY_RUN] 시뮬레이션 완료 - 실제 실행 전 검토 필요",
                data={
                    "action": (action.__name__ if hasattr(action, "__name__") else str(action)),
                    "args": str(args)[:100],
                    "kwargs": str(kwargs)[:100],
                    "mode": "dry_run",
                },
                trinity_impact=TRINITY_IMPACT,
            )
        else:
            try:
                if asyncio.iscoroutinefunction(action):
                    result = await action(*args, **kwargs)
                else:
                    result = action(*args, **kwargs)

                return PrincipleResult(
                    principle_id=3,
                    principle_name="병자궤도야",
                    classic=Classic.SUN_TZU,
                    success=True,
                    message="[WET_RUN] 실행 완료",
                    data={"result": str(result)[:200], "mode": "wet_run"},
                    trinity_impact=TRINITY_IMPACT,
                )
            except Exception as e:
                return PrincipleResult(
                    principle_id=3,
                    principle_name="병자궤도야",
                    classic=Classic.SUN_TZU,
                    success=False,
                    message=f"[WET_RUN] 실행 실패: {e}",
                    data={"error": str(e), "mode": "wet_run"},
                    trinity_impact=TRINITY_IMPACT,
                )

    async def principle_04_async_execute(self, tasks: list[Callable[..., Any]]) -> PrincipleResult:
        """[04] 병귀신속 (Speed is of Great Value)

        원칙: 응답 속도는 UX의 핵심. 느린 로직은 비동기로 처리하라.
        """
        return PrincipleResult(
            4,
            "병귀신속",
            Classic.SUN_TZU,
            True,
            f"{len(tasks)}개 작업 비동기 실행 준비",
            {"task_count": len(tasks)},
            TRINITY_IMPACT,
        )

    async def principle_05_trinity_alignment(
        self, truth_score: float, goodness_score: float, beauty_score: float
    ) -> PrincipleResult:
        """[05] 도천지장법 (The Five Factors)

        원칙: 프로젝트의 5요소가 정렬되었는지 확인하라.
        """
        trinity_score = 0.35 * truth_score + 0.35 * goodness_score + 0.20 * beauty_score
        aligned = trinity_score >= 0.70
        return PrincipleResult(
            5,
            "도천지장법",
            Classic.SUN_TZU,
            aligned,
            f"Trinity Score: {trinity_score:.2%}" + (" - 정렬됨" if aligned else " - 정렬 필요"),
            {
                "trinity_score": trinity_score,
                "眞": truth_score,
                "善": goodness_score,
                "美": beauty_score,
            },
            TRINITY_IMPACT,
        )

    async def principle_06_standard_then_custom(self) -> PrincipleResult:
        """[06] 정병 - 정석으로 공격하고, 변칙으로 승리하라."""
        return PrincipleResult(
            6, "정병", Classic.SUN_TZU, True, "표준 패턴 준수 후 오버라이딩", {}, TRINITY_IMPACT
        )

    async def principle_07_find_bottleneck(
        self, metrics: dict[str, float] | None = None
    ) -> PrincipleResult:
        """[07] 허실 - 시스템의 병목을 찾아 집중 보강하라."""
        metrics = metrics or {}
        bottleneck = min(metrics.items(), key=lambda x: x[1])[0] if metrics else "unknown"
        return PrincipleResult(
            7,
            "허실",
            Classic.SUN_TZU,
            True,
            f"병목 발견: {bottleneck}",
            {"metrics": metrics},
            TRINITY_IMPACT,
        )

    async def principle_08_exception_handler(self, error: Exception) -> PrincipleResult:
        """[08] 구변 - 예외 상황에 따라 유연하게 대처 경로를 바꿔라."""
        return PrincipleResult(
            8,
            "구변",
            Classic.SUN_TZU,
            True,
            f"예외 처리: {type(error).__name__}",
            {"error": str(error)},
            TRINITY_IMPACT,
        )

    async def principle_09_logging_spy(self, message: str, level: str = "info") -> PrincipleResult:
        """[09] 용간 - 로그와 모니터링은 적(Bug)을 알 수 있는 유일한 수단이다."""
        getattr(logger, level, logger.info)(f"[용간] {message}")
        return PrincipleResult(
            9,
            "용간",
            Classic.SUN_TZU,
            True,
            f"[{level.upper()}] 로그 기록 완료",
            {"message": message},
            TRINITY_IMPACT,
        )

    async def principle_10_dangerous_action_gate(
        self, action_name: str, confirmed: bool = False
    ) -> PrincipleResult:
        """[10] 화공 - 파괴적 행동은 확실한 이득이 있을 때만 수행하라."""
        return PrincipleResult(
            10,
            "화공",
            Classic.SUN_TZU,
            confirmed,
            f"위험 행동: {action_name}" + (" - 승인됨" if confirmed else " - 승인 필요"),
            {"confirmed": confirmed},
            TRINITY_IMPACT,
        )

    async def principle_11_mvp_deploy(self) -> PrincipleResult:
        """[11] 졸속 - 완벽하게 늦는 것보다, 부족해도 빨리 배포하고 고치는 게 낫다."""
        return PrincipleResult(
            11, "졸속", Classic.SUN_TZU, True, "MVP 배포 우선", {}, TRINITY_IMPACT
        )

    async def principle_12_full_automation(self) -> PrincipleResult:
        """[12] 부전이굴 - 최고의 자동화는 사용자가 아무것도 하지 않게 하는 것이다."""
        return PrincipleResult(
            12, "부전이굴", Classic.SUN_TZU, True, "완전 자동화 목표", {}, TRINITY_IMPACT
        )
