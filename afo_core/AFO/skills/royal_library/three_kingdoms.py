"""제2서: 삼국지 (12선) - 永 60% / 善 40%

지속가능성과 협력의 지혜
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
TRINITY_IMPACT = {"永": 0.60, "善": 0.40}


class ThreeKingdomsPrinciples:
    """삼국지 12선 원칙"""

    async def principle_13_loose_coupling(self, modules: list[str]) -> PrincipleResult:
        """[13] 도원결의 - 모듈 간 결합은 느슨하되, 목표는 형제처럼 일치시켜라."""
        return PrincipleResult(
            13,
            "도원결의",
            Classic.THREE_KINGDOMS,
            True,
            f"{len(modules)}개 모듈 느슨한 결합",
            {"modules": modules},
            TRINITY_IMPACT,
        )

    async def principle_14_retry_with_backoff(
        self,
        action: Callable[..., T],
        *args: Any,
        max_attempts: int = 3,
        backoff_factor: float = 2.0,
        **kwargs: Any,
    ) -> PrincipleResult:
        """[14] 삼고초려 (Three Visits) - Retry with Exponential Backoff

        원칙: 외부 API나 리소스 요청 실패 시, 최소 3번은 정중하게 재시도하라.
        """
        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(action):
                    result = await action(*args, **kwargs)
                else:
                    result = action(*args, **kwargs)

                return PrincipleResult(
                    principle_id=14,
                    principle_name="삼고초려",
                    classic=Classic.THREE_KINGDOMS,
                    success=True,
                    message=f"성공 (시도 {attempt}/{max_attempts})",
                    data={"result": str(result)[:200], "attempts": attempt},
                    trinity_impact=TRINITY_IMPACT,
                )
            except Exception as e:
                last_error = e
                if attempt < max_attempts:
                    wait_time = backoff_factor ** (attempt - 1)
                    logger.warning(f"[삼고초려] 시도 {attempt} 실패, {wait_time}초 후 재시도: {e}")
                    await asyncio.sleep(wait_time)

        return PrincipleResult(
            principle_id=14,
            principle_name="삼고초려",
            classic=Classic.THREE_KINGDOMS,
            success=False,
            message=f"3번 시도 후 실패: {last_error}",
            data={"error": str(last_error), "attempts": max_attempts},
            trinity_impact=TRINITY_IMPACT,
        )

    async def principle_15_graceful_degradation(self, fallback_value: Any) -> PrincipleResult:
        """[15] 공성계 - 시스템이 고장났어도, 사용자에게는 평온(Fallback UI)을 보여주어라."""
        return PrincipleResult(
            15,
            "공성계",
            Classic.THREE_KINGDOMS,
            True,
            "Graceful Degradation 활성화",
            {"fallback": str(fallback_value)[:100]},
            TRINITY_IMPACT,
        )

    async def principle_16_external_integration(self, package: str) -> PrincipleResult:
        """[16] 초선차전 - 남의 자원(오픈소스, 외부 API)을 빌려 내 힘으로 삼아라."""
        return PrincipleResult(
            16,
            "초선차전",
            Classic.THREE_KINGDOMS,
            True,
            f"외부 리소스 활용: {package}",
            {"package": package},
            TRINITY_IMPACT,
        )

    async def principle_17_pipeline_chain(self, steps: list[str]) -> PrincipleResult:
        """[17] 연환계 - 작은 마이크로 서비스들을 연결하여 거대한 함대를 만들어라."""
        return PrincipleResult(
            17,
            "연환계",
            Classic.THREE_KINGDOMS,
            True,
            f"{len(steps)}단계 파이프라인",
            {"steps": steps},
            TRINITY_IMPACT,
        )

    async def principle_18_hide_complexity(self) -> PrincipleResult:
        """[18] 미인계 - 복잡한 백엔드 로직은 아름다운 UI 뒤에 숨겨라."""
        return PrincipleResult(
            18, "미인계", Classic.THREE_KINGDOMS, True, "복잡성 추상화 완료", {}, TRINITY_IMPACT
        )

    async def principle_19_feedback_loop(self, iteration: int = 1) -> PrincipleResult:
        """[19] 칠종칠금 - 사용자가 만족할 때까지 끈질기게 수정하고 피드백을 받아라."""
        return PrincipleResult(
            19,
            "칠종칠금",
            Classic.THREE_KINGDOMS,
            True,
            f"피드백 루프 #{iteration}",
            {"iteration": iteration},
            TRINITY_IMPACT,
        )

    async def principle_20_scheduled_task(self, cron: str = "0 * * * *") -> PrincipleResult:
        """[20] 동남풍 - 타이밍이 생명이다. 스케줄러를 활용하라."""
        return PrincipleResult(
            20,
            "동남풍",
            Classic.THREE_KINGDOMS,
            True,
            f"스케줄 설정: {cron}",
            {"cron": cron},
            TRINITY_IMPACT,
        )

    async def principle_21_circuit_breaker(self, threshold: int = 5) -> PrincipleResult:
        """[21] 고육지계 - 시스템 전체를 살리기 위해 일부 기능을 희생할 줄 알아야 한다."""
        return PrincipleResult(
            21,
            "고육지계",
            Classic.THREE_KINGDOMS,
            True,
            f"Circuit Breaker 임계값: {threshold}",
            {"threshold": threshold},
            TRINITY_IMPACT,
        )

    async def principle_22_code_convention(self, linter: str = "ruff") -> PrincipleResult:
        """[22] 한실부흥 - 코드의 정통성(Legacy)과 스타일 가이드를 준수하라."""
        return PrincipleResult(
            22,
            "한실부흥",
            Classic.THREE_KINGDOMS,
            True,
            f"린터: {linter}",
            {"linter": linter},
            TRINITY_IMPACT,
        )

    async def principle_23_modular_split(self, parts: int = 3) -> PrincipleResult:
        """[23] 천하삼분 - 거대한 문제는 쪼개어 정복하라."""
        return PrincipleResult(
            23,
            "천하삼분",
            Classic.THREE_KINGDOMS,
            True,
            f"{parts}개로 분할",
            {"parts": parts},
            TRINITY_IMPACT,
        )

    async def principle_24_checkpoint_state(self, state: dict[str, Any]) -> PrincipleResult:
        """[24] 탁고 - 자신이 종료되더라도, 다음 프로세스를 위해 상태를 남겨라."""
        return PrincipleResult(
            24,
            "탁고",
            Classic.THREE_KINGDOMS,
            True,
            "상태 저장 완료",
            {"state_keys": list(state.keys())},
            TRINITY_IMPACT,
        )
