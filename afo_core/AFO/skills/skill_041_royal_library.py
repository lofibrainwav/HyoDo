"""AFO 왕립 도서관 41선 Skill/MCP (Re-export)

리팩터링: 500줄 규칙 준수를 위해 royal_library/ 패키지로 분리
기존 import 경로 호환성 유지

실제 구현:
- royal_library/models.py: Classic, PrincipleResult
- royal_library/sun_tzu.py: 손자병법 12선
- royal_library/three_kingdoms.py: 삼국지 12선
- royal_library/the_prince.py: 군주론 9선
- royal_library/on_war.py: 전쟁론 8선
"""

from AFO.skills.royal_library import (
    Classic,
    PrincipleResult,
    RoyalLibrarySkill,
    skill_041,
)

__all__ = [
    "Classic",
    "PrincipleResult",
    "RoyalLibrarySkill",
    "skill_041",
]
