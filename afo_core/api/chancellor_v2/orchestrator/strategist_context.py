"""Strategist Context - 독립 실행 컨텍스트.

각 Strategist는 자신만의 격리된 컨텍스트에서 실행되며,
Orchestrator를 통해서만 메인 상태와 통신합니다.

AFO 철학:
- 眞 (Truth): 타입 안전한 데이터클래스
- 善 (Goodness): 상태 격리로 부작용 방지
- 永 (Eternity): context_id로 추적 가능
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..graph.state import GraphState


@dataclass
class StrategistContext:
    """독립적인 서브에이전트 실행 컨텍스트.

    각 Strategist는 자신만의 격리된 컨텍스트에서 실행되며,
    Orchestrator를 통해서만 메인 상태와 통신합니다.

    Attributes:
        context_id: 고유 컨텍스트 식별자 (추적용)
        strategist_name: Strategist 이름 (예: "장영실")
        pillar: 담당 기둥 (TRUTH/GOODNESS/BEAUTY)

        # 입력 (읽기 전용)
        command: 원본 명령어
        plan: 실행 계획 (skill_id, query 포함)
        kingdom_dna: Context7 주입된 AFO 지식

        # 출력 (Strategist가 작성)
        score: 평가 점수 (0.0 ~ 1.0)
        reasoning: 평가 근거
        issues: 발견된 이슈 목록
        metadata: 추가 메타데이터

        # 실행 메타
        started_at: 실행 시작 시간
        completed_at: 실행 완료 시간
        errors: 발생한 에러 목록
    """

    # Identity
    context_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    strategist_name: str = ""
    pillar: str = ""  # TRUTH / GOODNESS / BEAUTY

    # Input (Read-only from GraphState)
    command: str = ""
    plan: dict[str, Any] = field(default_factory=dict)
    kingdom_dna: str = ""

    # Output (Written by Strategist)
    score: float = 0.0
    reasoning: str = ""
    issues: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Execution Meta
    started_at: float = field(default_factory=time.time)
    completed_at: float = 0.0
    errors: list[str] = field(default_factory=list)

    def mark_started(self) -> None:
        """실행 시작 시간 기록."""
        self.started_at = time.time()

    def mark_completed(self) -> None:
        """실행 완료 시간 기록."""
        self.completed_at = time.time()

    @property
    def duration_ms(self) -> float:
        """실행 시간 (밀리초)."""
        if self.completed_at > 0:
            return (self.completed_at - self.started_at) * 1000
        return 0.0

    @property
    def has_errors(self) -> bool:
        """에러 발생 여부."""
        return len(self.errors) > 0

    @property
    def skill_id(self) -> str:
        """Plan에서 skill_id 추출."""
        return self.plan.get("skill_id", "")

    @property
    def query(self) -> str:
        """Plan에서 query 추출."""
        return self.plan.get("query", "")

    def to_output_dict(self) -> dict[str, Any]:
        """GraphState.outputs 형식으로 변환."""
        return {
            "score": self.score,
            "reasoning": self.reasoning,
            "issues": self.issues,
            "metadata": {
                **self.metadata,
                "context_id": self.context_id,
                "strategist": self.strategist_name,
                "duration_ms": self.duration_ms,
            },
        }

    @classmethod
    def from_graph_state(
        cls,
        state: GraphState,
        strategist_name: str,
        pillar: str,
    ) -> StrategistContext:
        """GraphState로부터 컨텍스트 생성.

        Args:
            state: GraphState 인스턴스
            strategist_name: Strategist 이름
            pillar: 담당 기둥

        Returns:
            격리된 StrategistContext
        """
        return cls(
            strategist_name=strategist_name,
            pillar=pillar,
            command=state.input.get("command", ""),
            plan=state.plan.copy() if state.plan else {},
            kingdom_dna=state.plan.get("_kingdom_dna", "") if state.plan else "",
        )
