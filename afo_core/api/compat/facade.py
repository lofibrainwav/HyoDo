"""HTML Data Facade

HTML 데이터 통합 계층 (眞善美孝永 5기둥).
"""

from datetime import datetime
from typing import Any

from .models import HTMLSectionData


class HTMLDataFacade:
    """
    HTML 데이터 통합 계층 (眞善美孝永 5기둥)

    Trinity Score: 美 (Beauty) - 체계적 데이터 통합 구조
    """

    def __init__(self) -> None:
        self.section_cache: dict[str, HTMLSectionData] = {}
        self.last_updated: datetime | None = None

    def get_philosophy_data(self) -> dict[str, Any]:
        """철학 데이터 조회"""
        if self.section_cache.get("philosophy"):
            return self.section_cache["philosophy"].content

        from .providers.philosophy import PhilosophyDataProvider

        provider = PhilosophyDataProvider()
        data = provider.get_philosophy_data()
        self.section_cache["philosophy"] = HTMLSectionData(
            title="철학",
            content=data,
            icon="📚",
            metadata={"updated_at": datetime.now().isoformat()},
        )
        self.last_updated = datetime.now()
        return data

    def get_port_data(self) -> list[dict[str, str]]:
        """포트 데이터 조회"""
        if self.section_cache.get("ports"):
            return self.section_cache["ports"].content

        from .providers.port import PortDataProvider

        provider = PortDataProvider()
        data = provider.get_port_data()
        self.section_cache["ports"] = HTMLSectionData(
            title="서비스 포트",
            content=data,
            icon="🔌",
            metadata={"updated_at": datetime.now().isoformat()},
        )
        self.last_updated = datetime.now()
        return data

    def get_persona_data(self) -> list[dict[str, str]]:
        """페르소나 데이터 조회"""
        if self.section_cache.get("personas"):
            return self.section_cache["personas"].content

        return [
            {
                "name": "승상",
                "code": "Chancellor",
                "role": "3책사 병렬 오케스트레이터",
            },
            {
                "name": "제갈량",
                "code": "JangYeongSil",
                "role": "眞 18% - 아키텍처/전략",
            },
            {
                "name": "사마의",
                "code": "YiSunSin",
                "role": "善 18% - 윤리/안정/보안",
            },
            {
                "name": "주유",
                "code": "ShinSaimdang",
                "role": "美 12% - 서사/UX/디자인",
            },
            {
                "name": "자룡",
                "code": "Bangtong",
                "role": "Codex - 구현/실행/프로토타입",
            },
            {
                "name": "방통",
                "code": "Jaryong",
                "role": "Claude - 논리/검증/리팩터링",
            },
        ]

    def get_personas_data(self) -> list[dict[str, str]]:
        """페르소나 데이터 조회 (복수형 alias)"""
        return self.get_persona_data()

    def get_royal_rules_data(self) -> list[dict[str, str]]:
        """왕국 규칙 데이터 조회"""
        if self.section_cache.get("rules"):
            return self.section_cache["rules"].content

        return [
            {
                "name": "眞善美孝永 5기둥",
                "description": "왕국 핵심 철학 시스템",
            },
            {
                "name": "Trinity Score",
                "description": "95+ AUTO_RUN, 70-89 ASK_COMMANDER, <70 BLOCK",
            },
            {
                "name": "Chancellor Orchestrator",
                "description": "3책사 병렬 평가 시스템",
            },
            {
                "name": "10초 프로토콜",
                "description": "작업 시작 시 반드시 출력해야 할 프로토콜",
            },
            {
                "name": "지피지기",
                "description": "SSOT 순차 확인 (AFO_FINAL_SSOT.md → AFO_ROYAL_LIBRARY.md)",
            },
            {
                "name": "Dry_Run",
                "description": "DB/삭제/배포 전 시뮬레이션",
            },
            {
                "name": "Historian",
                "description": "결정 근거와 실행 커맨드 기록",
            },
        ]

    def get_architecture_data(self) -> dict[str, Any]:
        """아키텍처 데이터 조회"""
        if self.section_cache.get("architecture"):
            return self.section_cache["architecture"].content

        return {
            "organs": {
                "name": "오장육부",
                "items": [
                    {"name": "심장 (Heart)", "role": "캐시/세션", "implementation": "Redis 6379"},
                    {
                        "name": "간 (Liver)",
                        "role": "영구 저장",
                        "implementation": "PostgreSQL 15432",
                    },
                    {
                        "name": "비장 (Spleen)",
                        "role": "AI 모델 서빙",
                        "implementation": "Ollama 11434",
                    },
                    {
                        "name": "폐 (Lungs)",
                        "role": "벡터 저장소",
                        "implementation": "LanceDB (파일)",
                    },
                    {"name": "신장 (Kidneys)", "role": "외부 연결", "implementation": "MCP"},
                ],
            },
            "pillars": [
                {"name": "眞", "weight": 35, "role": "기술적 확실성/타입 안전성"},
                {"name": "善", "weight": 35, "role": "보안/리스크/PII 보호"},
                {"name": "美", "weight": 20, "role": "단순함/일관성/구조화"},
                {"name": "孝", "weight": 8, "role": "평온 수호/운영 마찰 제거"},
                {"name": "永", "weight": 2, "role": "영속성/결정 기록"},
            ],
            "strategists": [
                {"name": "제갈량", "pillar": "眞", "weight": 35, "symbol": "⚔️"},
                {"name": "사마의", "pillar": "善", "weight": 35, "symbol": "🛡️"},
                {"name": "주유", "pillar": "美", "weight": 20, "symbol": "🌉"},
            ],
        }

    def get_stats_data(self) -> dict[str, int]:
        """통계 데이터 조회"""
        if self.section_cache.get("stats"):
            return self.section_cache["stats"].content

        return {
            "total_files": 793,
            "active_sessions": 12,
            "trinity_score": 94.63,
            "last_update": "2026-01-17",
        }

    def invalidate_cache(self, section: str | None = None) -> None:
        """캐시 무효화"""
        if section:
            self.section_cache.pop(section, None)
        else:
            self.section_cache.clear()
        self.last_updated = datetime.now()

    def get_cache_status(self) -> dict[str, Any]:
        """캐시 상태 조회"""
        return {
            "cache_keys": list(self.section_cache.keys()),
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "total_sections": len(self.section_cache),
        }
