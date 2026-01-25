"""AFO 왕립 도서관 41선 Skill/MCP

4대 고전(손자병법/삼국지/군주론/전쟁론)의 전략적 지혜를 실행 가능한 도구로

리팩터링: 500줄 규칙 준수를 위해 모듈 분리
- models.py: Classic, PrincipleResult
- sun_tzu.py: 손자병법 12선
- three_kingdoms.py: 삼국지 12선
- the_prince.py: 군주론 9선
- on_war.py: 전쟁론 8선
"""

from __future__ import annotations

import logging
from typing import Any

from AFO.skills.royal_library.models import Classic, PrincipleResult
from AFO.skills.royal_library.on_war import OnWarPrinciples
from AFO.skills.royal_library.sun_tzu import SunTzuPrinciples
from AFO.skills.royal_library.the_prince import ThePrincePrinciples
from AFO.skills.royal_library.three_kingdoms import ThreeKingdomsPrinciples

logger = logging.getLogger(__name__)

__all__ = [
    "Classic",
    "PrincipleResult",
    "RoyalLibrarySkill",
    "skill_041",
]


class RoyalLibrarySkill(
    SunTzuPrinciples, ThreeKingdomsPrinciples, ThePrincePrinciples, OnWarPrinciples
):
    """AFO 왕립 도서관 41선 Skill

    4대 고전의 전략적 지혜:
    - 손자병법 (12선): 眞 70% / 孝 30%
    - 삼국지 (12선): 永 60% / 善 40%
    - 군주론 (9선): 善 50% / 眞 50%
    - 전쟁론 (8선): 眞 60% / 孝 40%
    """

    def __init__(self) -> None:
        self.principles_count = 41
        logger.info("📜 [왕립도서관] 41선 Skill 초기화 완료")

    def get_principle_info(self, principle_id: int) -> dict[str, Any]:
        """원칙 정보 조회"""
        principles = {
            1: {"name": "지피지기", "classic": "손자병법", "tool": "preflight_check"},
            3: {"name": "병자궤도야", "classic": "손자병법", "tool": "dry_run_simulation"},
            14: {"name": "삼고초려", "classic": "삼국지", "tool": "retry_with_backoff"},
            25: {"name": "사랑보다두려움", "classic": "군주론", "tool": "strict_typing"},
            34: {"name": "전장의안개", "classic": "전쟁론", "tool": "null_check_validation"},
            36: {"name": "중심", "classic": "전쟁론", "tool": "root_cause_analysis"},
        }
        return principles.get(principle_id, {"name": "미구현", "classic": "N/A"})

    def list_implemented_principles(self) -> list[int]:
        """구현된 원칙 목록"""
        return [1, 3, 14, 25, 34, 36]


# Singleton export
skill_041 = RoyalLibrarySkill()


if __name__ == "__main__":
    import asyncio

    async def test_royal_library() -> None:
        print("📜 Royal Library 41선 Skill 테스트")
        print("=" * 50)

        # 01. 지피지기 테스트
        result = await skill_041.principle_01_preflight_check(
            sources=["doc1", "doc2"], context={"system": "ready"}
        )
        print(f"\n[01] 지피지기: {result.message}")

        # 03. 병자궤도야 테스트
        result = await skill_041.principle_03_dry_run_simulation(lambda x: x * 2, 5, simulate=True)
        print(f"[03] 병자궤도야: {result.message}")

        # 25. 사랑보다두려움 테스트
        result = await skill_041.principle_25_strict_typing("hello", str)
        print(f"[25] 사랑보다두려움: {result.message}")

        # 34. 전장의안개 테스트
        result = await skill_041.principle_34_null_check_validation(
            {"name": "test", "value": 42}, required_fields=["name", "value"]
        )
        print(f"[34] 전장의안개: {result.message}")

        print("\n✅ 테스트 완료!")

    asyncio.run(test_royal_library())
