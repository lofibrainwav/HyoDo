# Trinity Score: 90.0 (Persona Service Types)
"""
페르소나 서비스 TypedDict 정의
眞 (Truth): 정밀한 타입 계약
善 (Goodness): 페르소나 타입 안전성
"""

from typing import Any, TypedDict


class TrinityScores(TypedDict, total=False):
    """Trinity Score 데이터."""

    truth: float
    goodness: float
    beauty: float
    serenity: float
    eternity: float


class SwitchResult(TypedDict, total=False):
    """페르소나 전환 결과."""

    current_persona: str
    status: str
    trinity_scores: TrinityScores
    last_switched: str | None


class PersonaInfo(TypedDict, total=False):
    """페르소나 정보."""

    id: str
    name: str
    type: str
    trinity_scores: TrinityScores
    active: bool
    last_switched: str | None


class TrinityScoreAnalysis(TypedDict, total=False):
    """Trinity Score 분석 결과."""

    truth_score: float
    goodness_score: float
    beauty_score: float
    serenity_score: float
    eternity_score: float
    total_score: float
    persona_type: str
    context_used: bool
    calculated_at: str
    evaluation: str
    error: str


class PersonaContext(TypedDict, total=False):
    """페르소나 맥락 정보."""

    source: str
    reason: str
    metadata: dict[str, Any]


class LogEntry(TypedDict, total=False):
    """로그 엔트리."""

    event: str
    persona_id: str
    persona_name: str
    persona_type: str
    trinity_scores: TrinityScores
    context: PersonaContext
    timestamp: str


class SSEEvent(TypedDict, total=False):
    """SSE 이벤트."""

    type: str
    data: LogEntry
    timestamp: str
