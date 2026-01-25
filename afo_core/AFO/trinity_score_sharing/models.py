"""Trinity Score Sharing System Models

Trinity Score 공유 시스템에서 사용되는 데이터 모델들.
"""

from dataclasses import dataclass


@dataclass
class TrinityScoreUpdate:
    """Trinity Score 업데이트 이벤트"""

    agent_type: str
    session_id: str
    previous_score: float
    new_score: float
    change_reason: str
    contributing_factors: dict[str, float]
    timestamp: str
    collaboration_impact: float = 0.0


@dataclass
class CollaborationMetrics:
    """협업 메트릭 데이터"""

    session_id: str
    agent_contributions: dict[str, int]
    consensus_level: float
    efficiency_gain: float
    trinity_score_variance: float
    collaboration_quality: str
    timestamp: str
