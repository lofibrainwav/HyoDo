"""제4서: 전쟁론 (8선) - 眞 60% / 孝 40%

불확실성 속의 의사결정과 리소스 관리의 지혜
"""

from __future__ import annotations

from typing import Any

from AFO.skills.royal_library.models import Classic, PrincipleResult

# Trinity 가중치
TRINITY_IMPACT = {"眞": 0.60, "孝": 0.40}


class OnWarPrinciples:
    """전쟁론 8선 원칙"""

    async def principle_34_null_check_validation(
        self, data: Any, required_fields: list[str] | None = None
    ) -> PrincipleResult:
        """[34] 전장의 안개 (Fog of War) - Null Check & Validation

        원칙: 정보(Data)가 없으면 움직이지 말고(Block), 정찰(Fetch)하라.
        """
        if data is None:
            return PrincipleResult(
                principle_id=34,
                principle_name="전장의안개",
                classic=Classic.ON_WAR,
                success=False,
                message="[BLOCK] 데이터 없음 - 정찰 필요",
                data={"reason": "null_data"},
                trinity_impact=TRINITY_IMPACT,
            )

        if required_fields:
            missing = []
            if isinstance(data, dict):
                missing = [f for f in required_fields if f not in data or data[f] is None]

            if missing:
                return PrincipleResult(
                    principle_id=34,
                    principle_name="전장의안개",
                    classic=Classic.ON_WAR,
                    success=False,
                    message=f"[BLOCK] 필수 필드 누락: {missing}",
                    data={"missing_fields": missing},
                    trinity_impact=TRINITY_IMPACT,
                )

        return PrincipleResult(
            principle_id=34,
            principle_name="전장의안개",
            classic=Classic.ON_WAR,
            success=True,
            message="데이터 검증 완료 - 진군 허가",
            data={"validated": True},
            trinity_impact=TRINITY_IMPACT,
        )

    async def principle_35_complexity_estimate(
        self, task: str, factors: int = 3
    ) -> PrincipleResult:
        """[35] 마찰 - 이론상 쉬워 보여도 실제로는 어렵다. 마찰계수를 계산하라."""
        return PrincipleResult(
            35,
            "마찰",
            Classic.ON_WAR,
            True,
            f"마찰 요소: {factors}개 (작업: {task[:30]})",
            {"task": task, "factors": factors},
            TRINITY_IMPACT,
        )

    async def principle_36_root_cause_analysis(
        self, symptoms: list[str], context: dict[str, Any] | None = None
    ) -> PrincipleResult:
        """[36] 중심 (Center of Gravity) - Root Cause Analysis

        원칙: 문제의 핵심 원인(Root Cause) 하나를 타격하라.
        """
        context = context or {}

        common_causes = {
            "timeout": "네트워크 또는 서버 응답 지연",
            "null": "데이터 누락 또는 초기화 실패",
            "permission": "권한 부족",
            "type": "타입 불일치",
            "connection": "연결 실패",
        }

        identified_causes = []
        for symptom in symptoms:
            symptom_lower = symptom.lower()
            for keyword, cause in common_causes.items():
                if keyword in symptom_lower:
                    identified_causes.append(cause)

        if identified_causes:
            root_cause = max(set(identified_causes), key=identified_causes.count)
            return PrincipleResult(
                principle_id=36,
                principle_name="중심",
                classic=Classic.ON_WAR,
                success=True,
                message=f"핵심 원인 식별: {root_cause}",
                data={"root_cause": root_cause, "all_causes": list(set(identified_causes))},
                trinity_impact=TRINITY_IMPACT,
            )
        else:
            return PrincipleResult(
                principle_id=36,
                principle_name="중심",
                classic=Classic.ON_WAR,
                success=False,
                message="핵심 원인 미식별 - 추가 정찰 필요",
                data={"symptoms": symptoms},
                trinity_impact=TRINITY_IMPACT,
            )

    async def principle_37_resource_monitor(self, usage_percent: float) -> PrincipleResult:
        """[37] 공세 종말점 - 리소스가 고갈되기 직전에 멈추고 재정비하라."""
        safe = usage_percent < 80
        return PrincipleResult(
            37,
            "공세종말점",
            Classic.ON_WAR,
            safe,
            f"리소스: {usage_percent:.1f}%" + (" ✅" if safe else " ⚠️ 재정비 필요"),
            {"usage": usage_percent},
            TRINITY_IMPACT,
        )

    async def principle_38_singleton_lock(self, resource: str) -> PrincipleResult:
        """[38] 지휘 통일 - 명령 권한은 하나여야 한다. 중복 실행을 막아라."""
        return PrincipleResult(
            38,
            "지휘통일",
            Classic.ON_WAR,
            True,
            f"싱글톤 락: {resource}",
            {"resource": resource},
            TRINITY_IMPACT,
        )

    async def principle_39_token_optimize(self, tokens: int, limit: int = 4096) -> PrincipleResult:
        """[39] 병력 절약 - 중요하지 않은 곳에 토큰을 낭비하지 마라."""
        efficient = tokens <= limit
        return PrincipleResult(
            39,
            "병력절약",
            Classic.ON_WAR,
            efficient,
            f"토큰: {tokens}/{limit}" + (" ✅" if efficient else " ⚠️"),
            {"tokens": tokens, "limit": limit},
            TRINITY_IMPACT,
        )

    async def principle_40_auto_run_gate(
        self, confidence: float, threshold: float = 0.8
    ) -> PrincipleResult:
        """[40] 대담함 - 확률이 높다면, 과감하게 자동화를 질러라."""
        auto_run = confidence >= threshold
        return PrincipleResult(
            40,
            "대담함",
            Classic.ON_WAR,
            auto_run,
            f"신뢰도: {confidence:.0%}" + (" → AUTO_RUN" if auto_run else " → 수동 확인"),
            {"confidence": confidence, "threshold": threshold},
            TRINITY_IMPACT,
        )

    async def principle_41_business_alignment(self, business_value: str) -> PrincipleResult:
        """[41] 전쟁은 정치의 연속 - 코드는 결국 비즈니스 요구사항을 실현하기 위한 도구이다."""
        return PrincipleResult(
            41,
            "정치연속",
            Classic.ON_WAR,
            True,
            f"비즈니스 가치: {business_value}",
            {"value": business_value},
            TRINITY_IMPACT,
        )
