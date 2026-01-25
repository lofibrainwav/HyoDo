"""AFO 왕립 도서관 - 모델 정의

4대 고전의 Trinity 가중치 및 결과 데이터 클래스
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Classic(Enum):
    """4대 고전"""

    SUN_TZU = "손자병법"  # 眞 70% / 孝 30%
    THREE_KINGDOMS = "삼국지"  # 永 60% / 善 40%
    THE_PRINCE = "군주론"  # 善 50% / 眞 50%
    ON_WAR = "전쟁론"  # 眞 60% / 孝 40%


@dataclass
class PrincipleResult:
    """원칙 실행 결과"""

    principle_id: int
    principle_name: str
    classic: Classic
    success: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    trinity_impact: dict[str, float] = field(default_factory=dict)
