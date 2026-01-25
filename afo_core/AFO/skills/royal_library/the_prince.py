"""제3서: 군주론 (9선) - 善 50% / 眞 50%

현실주의적 통치와 타입 안전성의 지혜
"""

from __future__ import annotations

from typing import Any

from AFO.skills.royal_library.models import Classic, PrincipleResult

# Trinity 가중치
TRINITY_IMPACT = {"善": 0.50, "眞": 0.50}


class ThePrincePrinciples:
    """군주론 9선 원칙"""

    async def principle_25_strict_typing(
        self, value: Any, expected_type: type, allow_none: bool = False
    ) -> PrincipleResult:
        """[25] 사랑보다 두려움 (Feared > Loved) - Strict Typing

        원칙: 느슨한 타입보다는 엄격한 타입(MyPy)이 낫다.
        """
        if value is None and allow_none:
            return PrincipleResult(
                principle_id=25,
                principle_name="사랑보다두려움",
                classic=Classic.THE_PRINCE,
                success=True,
                message="None 허용됨",
                data={"value": None, "expected": expected_type.__name__},
                trinity_impact=TRINITY_IMPACT,
            )

        if isinstance(value, expected_type):
            return PrincipleResult(
                principle_id=25,
                principle_name="사랑보다두려움",
                classic=Classic.THE_PRINCE,
                success=True,
                message=f"타입 검증 통과: {expected_type.__name__}",
                data={"value": str(value)[:100], "type": type(value).__name__},
                trinity_impact=TRINITY_IMPACT,
            )
        else:
            return PrincipleResult(
                principle_id=25,
                principle_name="사랑보다두려움",
                classic=Classic.THE_PRINCE,
                success=False,
                message=f"타입 불일치: {type(value).__name__} != {expected_type.__name__}",
                data={"actual_type": type(value).__name__, "expected_type": expected_type.__name__},
                trinity_impact=TRINITY_IMPACT,
            )

    async def principle_26_error_control(self) -> PrincipleResult:
        """[26] 비르투와 포르투나 - 운에 맡기지 말고, 실력(Error Handling)으로 통제하라."""
        return PrincipleResult(
            26, "비르투", Classic.THE_PRINCE, True, "Exception Handling 강화", {}, TRINITY_IMPACT
        )

    async def principle_27_algorithm_select(self, options: list[str]) -> PrincipleResult:
        """[27] 여우와 사자 - 때로는 교활하게, 때로는 강력하게 해결하라."""
        return PrincipleResult(
            27,
            "여우와사자",
            Classic.THE_PRINCE,
            True,
            f"알고리즘 옵션: {options}",
            {"options": options},
            TRINITY_IMPACT,
        )

    async def principle_28_ux_friction_check(self, friction_score: float) -> PrincipleResult:
        """[28] 증오 피하기 - 사용자에게 불쾌감(Friction > 30)을 주면 반란(이탈)의 지름길이다."""
        safe = friction_score <= 30
        return PrincipleResult(
            28,
            "증오피하기",
            Classic.THE_PRINCE,
            safe,
            f"Friction: {friction_score}" + (" ✅" if safe else " ⚠️"),
            {"friction": friction_score},
            TRINITY_IMPACT,
        )

    async def principle_29_executable_code_only(self) -> PrincipleResult:
        """[29] 무장한 예언자 - 코드 없는 아이디어는 패배한다. 실행 가능한 코드만 가치가 있다."""
        return PrincipleResult(
            29, "무장한예언자", Classic.THE_PRINCE, True, "Executable Code Only", {}, TRINITY_IMPACT
        )

    async def principle_30_garbage_collect(self) -> PrincipleResult:
        """[30] 잔인함의 효율적 사용 - 좀비 프로세스나 낭비 자원은 가차 없이 죽여라."""
        return PrincipleResult(
            30, "잔인함", Classic.THE_PRINCE, True, "Garbage Collection 완료", {}, TRINITY_IMPACT
        )

    async def principle_31_uptime_monitor(self, uptime_percent: float = 99.9) -> PrincipleResult:
        """[31] 국가 유지 - 시스템의 Uptime 유지가 군주의 제1덕목이다."""
        return PrincipleResult(
            31,
            "국가유지",
            Classic.THE_PRINCE,
            uptime_percent >= 99.0,
            f"Uptime: {uptime_percent}%",
            {"uptime": uptime_percent},
            TRINITY_IMPACT,
        )

    async def principle_32_model_router(self, models: list[str]) -> PrincipleResult:
        """[32] 현명한 조언자 - 좋은 모델을 선택하고, 나쁜 모델은 걸러라."""
        return PrincipleResult(
            32,
            "현명한조언자",
            Classic.THE_PRINCE,
            True,
            f"모델 풀: {models}",
            {"models": models},
            TRINITY_IMPACT,
        )

    async def principle_33_creative_solution(self, trinity_score: float) -> PrincipleResult:
        """[33] 결과가 수단을 정당화 - Trinity Score > 90이면 파격적 방법도 허용한다."""
        allowed = trinity_score >= 0.90
        return PrincipleResult(
            33,
            "결과정당화",
            Classic.THE_PRINCE,
            allowed,
            f"Trinity: {trinity_score:.0%}" + (" - 파격 허용" if allowed else " - 정석 유지"),
            {"trinity_score": trinity_score},
            TRINITY_IMPACT,
        )
