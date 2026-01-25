from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
"""Framework Selector - Mission Profile 기반 자동 프레임워크 선택
眞善美孝: Truth, Goodness, Beauty, Serenity

메타인지 기반 의사결정:
- 복잡도 + 신뢰도 + 비용 감수도 기반 최적 프레임워크 선택
- 캐싱으로 재계산 최소화
- 미래 확장성 고려 (프레임워크 추가 용이)
"""


class FrameworkName(str, Enum):
    AUTOGEN = "autogen"
    CREWAI = "crewai"
    LANGGRAPH = "langgraph"


@dataclass(frozen=True)
class MissionProfile:
    """미션 프로필 - 프레임워크 선택 기준"""

    mission_type: str  # "research", "analysis", "workflow", "coding", "planning"
    complexity: int  # 1~5 (1: 매우 단순, 5: 매우 복잡)
    reliability: int  # 1~5 (1: 낮음, 5: 매우 높음)
    latency_sensitivity: int = 3  # 1~5 (1: 느려도 OK, 5: 매우 빠름)
    cost_sensitivity: int = 3  # 1~5 (1: 비용 OK, 5: 매우 절감)


@lru_cache(maxsize=512)
def select_framework(profile: MissionProfile) -> FrameworkName:
    """미션 프로필 기반 최적 프레임워크 선택

    선택 로직 (메타인지 기반):
    - LangGraph: 복잡 + 신뢰 우선 (엔터프라이즈급)
    - AutoGen: 연구/분석, 지연 허용 (깊은 탐구)
    - CrewAI: 속도 + 비용 우선 (실용적)

    Args:
        profile: 미션 프로필

    Returns:
        FrameworkName: 선택된 프레임워크

    """
    # 眞(진): 복잡하고 신뢰할 수 있어야 하는 미션
    if profile.complexity >= 4 and profile.reliability >= 4:
        return FrameworkName.LANGGRAPH

    # 善(선): 깊은 연구/분석, 지연 허용
    if profile.mission_type in {"research", "analysis", "deep_dive"}:
        if profile.latency_sensitivity <= 3:  # 지연 감수 OK
            return FrameworkName.AUTOGEN
        return FrameworkName.CREWAI

    # 美(미): 비용 효율성 우선
    if profile.cost_sensitivity >= 4:
        return FrameworkName.CREWAI

    # 孝(효): 단순 작업, 빠른 결과
    if profile.complexity <= 2:
        return FrameworkName.CREWAI

    # 기본값: 균형 잡힌 선택
    return FrameworkName.AUTOGEN


# 글로벌 인스턴스 (편의성)
selector = select_framework


# 테스트용 헬퍼 함수
def demo_selector() -> None:
    """데모: 다양한 프로필로 테스트"""
    profiles = [
        MissionProfile("research", 4, 3, 2, 3),  # → AUTOGEN
        MissionProfile("workflow", 5, 5, 4, 2),  # → LANGGRAPH
        MissionProfile("simple_task", 2, 3, 5, 4),  # → CREWAI
    ]

    for profile in profiles:
        fw = select_framework(profile)
        print(f"{profile.mission_type}: {fw.value}")


if __name__ == "__main__":
    demo_selector()
