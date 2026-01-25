from __future__ import annotations

from typing import Final, TypedDict

from AFO.config.trinity import Pillar, TrinityConfig

# Trinity Score: 90.0 (Established by Chancellor)
"""AFO 왕국 헌법 v1.0 - 성스러운 봉인
Sealed: 2025-12-22



이 파일은 AFO 왕국의 근본 법칙을 정의하며,
Chancellor Graph의 AUTO_RUN/ASK 라우팅의 영원한 기준선입니다.
"""


class TrinityWeights(TypedDict):
    """5기둥 가중치 정의 (眞·善·美·孝·永)"""

    truth: float  # 眞 - 기술적 정확성
    goodness: float  # 善 - 윤리·안정성
    beauty: float  # 美 - 구조적 우아함
    serenity: float  # 孝 - 사용자 마찰 제거
    eternity: float  # 永 - 영속성·기록 보존


# AFO 왕국 헌법 v1.0 - 2025-12-22 성스러운 봉인
AFO_CONSTITUTION_V1_0: Final[dict] = {
    "version": "1.0",
    "sealed_date": "2025-12-22",
    "description": "AFO Kingdom Constitution v1.0 - Harmony Level Achieved",
    "trinity_weights": TrinityWeights(
        truth=TrinityConfig.get_weight(Pillar.TRUTH),  # 眞
        goodness=TrinityConfig.get_weight(Pillar.GOODNESS),  # 善
        beauty=TrinityConfig.get_weight(Pillar.BEAUTY),  # 美
        serenity=TrinityConfig.get_weight(Pillar.SERENITY),  # 孝
        eternity=TrinityConfig.get_weight(Pillar.ETERNITY),  # 永
    ),
    "auto_run_threshold": 90.0,  # Trinity Score >= 90.0
    "risk_threshold": 10.0,  # Risk Score <= 10.0
    "veto_threshold": 40.0,  # 개별 pillar < 40.0이면 강제 거부
    "veto_pillars": ["truth", "goodness", "beauty"],  # 거부권 행사 pillar들
    "royal_library_principles": 41,  # 41선 원칙 준수
    "current_amendment": "0001",  # 현재 적용 수정헌법
    "harmony_achieved": {
        "mcp_ecosystem": 9,  # MCP 9서버 통합
        "skills_registry": 19,  # Skills 19개
        "context7_integration": 12,  # Context7 12개
        "antigravity_sync": True,  # Antigravity 동기화
        "chancellor_graph": True,  # Chancellor Graph 완성
    },
}

# 현재 적용 버전 (런타임 참조용)
CURRENT_CONSTITUTION_VERSION: Final[str] = "1.0"

# 헌법 상수들 (런타임 최적화용)
TRINITY_WEIGHTS: Final[TrinityWeights] = AFO_CONSTITUTION_V1_0["trinity_weights"]
AUTO_RUN_THRESHOLD: Final[float] = AFO_CONSTITUTION_V1_0["auto_run_threshold"]
RISK_THRESHOLD: Final[float] = AFO_CONSTITUTION_V1_0["risk_threshold"]
VETO_THRESHOLD: Final[float] = AFO_CONSTITUTION_V1_0["veto_threshold"]
VETO_PILLARS: Final[list[str]] = AFO_CONSTITUTION_V1_0["veto_pillars"]

# 내보내기
__all__ = [
    "AFO_CONSTITUTION_V1_0",
    "AUTO_RUN_THRESHOLD",
    "CURRENT_CONSTITUTION_VERSION",
    "RISK_THRESHOLD",
    "TRINITY_WEIGHTS",
    "VETO_PILLARS",
    "VETO_THRESHOLD",
    "TrinityWeights",
]
