# Trinity Score: 90.0 (Established by Chancellor)
"""Persona Domain Model
TRINITY-OS Personas 시스템 - Family Hub OS Phase 1 핵심
PDF 페이지 4: "TRINITY-OS의 페르소나(Personas) 시스템" + 페이지 3: 로그 브릿지
"""

import sys
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PersonaType(str, Enum):
    """페르소나 타입 (眞善美孝永)"""

    COMMANDER = "commander"  # 사령관 (전략·통제)
    FAMILY_HEAD = "family_head"  # 가장 (인·따뜻함)
    CREATOR = "creator"  # 창작자 (美·몰입)
    LEARNER = "learner"  # 배움의 길 (眞·탐구)
    JANG_YEONG_SIL = "jang_yeong_sil"  # 제갈량 (眞 Truth)
    YI_SUN_SIN = "yi_sun_sin"  # 사마의 (善 Goodness)
    SHIN_SAIMDANG = "shin_saimdang"  # 주유 (美 Beauty)


class Persona(BaseModel):
    """형님의 각 역할을 디지털로 구현한 페르소나 모델 (眞善美孝永)

    PDF 페이지 4: "TRINITY-OS의 페르소나(Personas) 시스템"
    PDF 페이지 3: 로그 브릿지 연계
    """

    id: str = Field(..., description="페르소나 ID")
    type: PersonaType = Field(..., description="페르소나 타입")
    name: str = Field(..., description="페르소나 이름 (예: '불굴의 사령관', '따뜻한 가장')")
    trinity_scores: dict[str, float] = Field(
        default_factory=lambda: {
            "truth": 100.0,
            "goodness": 100.0,
            "beauty": 100.0,
            "serenity": 100.0,
            "eternity": 100.0,
        },
        description="眞善美孝永 점수 (PDF 페이지 3: 5대 기둥 적용)",
    )
    active: bool = Field(default=False, description="활성 상태")
    last_switched: datetime | None = Field(default=None, description="마지막 전환 시간")
    context_memory: list[dict[str, Any]] = Field(
        default_factory=list, description="최근 10개 대화 (로그 브릿지 연계)"
    )

    def switch_to(self) -> None:
        """페르소나 전환 - TRINITY-OS와 실시간 동기화
        PDF 페이지 3: 로그 브릿지
        """
        try:
            self.active = True
            self.last_switched = datetime.now(UTC)
            # 메모리 제한 (孝: 인지 마찰 제거)
            self.context_memory = self.context_memory[-10:]
            print(f"[TRINITY-OS] 페르소나 전환 → {self.name} (활성화)", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] 페르소나 전환 실패: {e}", file=sys.stderr)
            raise

    def add_context(self, context: dict[str, Any]) -> None:
        """맥락 정보 추가 (로그 브릿지용)"""
        self.context_memory.append(
            {
                **context,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        # 최대 10개 유지
        if len(self.context_memory) > 10:
            self.context_memory = self.context_memory[-10:]


# 형님 전용 페르소나 인스턴스 (싱글톤)
commander = Persona(
    id="p001",
    type=PersonaType.COMMANDER,
    name="불굴의 사령관",
    trinity_scores={
        "truth": 100.0,
        "goodness": 95.0,
        "beauty": 90.0,
        "serenity": 100.0,
        "eternity": 98.0,
    },
)

family_head = Persona(
    id="p002",
    type=PersonaType.FAMILY_HEAD,
    name="따뜻한 가장",
    trinity_scores={
        "truth": 90.0,
        "goodness": 100.0,
        "beauty": 98.0,
        "serenity": 100.0,
        "eternity": 95.0,
    },
)

creator = Persona(
    id="p003",
    type=PersonaType.CREATOR,
    name="창조의 불꽃",
    trinity_scores={
        "truth": 95.0,
        "goodness": 90.0,
        "beauty": 100.0,
        "serenity": 98.0,
        "eternity": 97.0,
    },
)

jang_yeong_sil = Persona(
    id="p004",
    type=PersonaType.JANG_YEONG_SIL,
    name="제갈량 (眞 Truth)",
    trinity_scores={
        "truth": 100.0,
        "goodness": 85.0,
        "beauty": 80.0,
        "serenity": 90.0,
        "eternity": 95.0,
    },
)

yi_sun_sin = Persona(
    id="p005",
    type=PersonaType.YI_SUN_SIN,
    name="사마의 (善 Goodness)",
    trinity_scores={
        "truth": 85.0,
        "goodness": 100.0,
        "beauty": 80.0,
        "serenity": 95.0,
        "eternity": 90.0,
    },
)

shin_saimdang = Persona(
    id="p006",
    type=PersonaType.SHIN_SAIMDANG,
    name="주유 (美 Beauty)",
    trinity_scores={
        "truth": 80.0,
        "goodness": 85.0,
        "beauty": 100.0,
        "serenity": 90.0,
        "eternity": 95.0,
    },
)

learner = Persona(
    id="p007",
    type=PersonaType.LEARNER,
    name="배움의 길 (眞 Learning)",
    trinity_scores={
        "truth": 100.0,
        "goodness": 95.0,
        "beauty": 85.0,
        "serenity": 97.0,
        "eternity": 100.0,
    },
)

# 현재 활성화된 페르소나 (기본: 사령관)
current_persona: Persona = commander
current_persona.switch_to()
