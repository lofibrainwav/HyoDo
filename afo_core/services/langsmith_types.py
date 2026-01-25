# Trinity Score: 95.0 (LangSmith Mentor Types)
"""
LangSmith 선생 시스템 TypedDict 정의
眞 (Truth): 정밀한 타입 계약
善 (Goodness): 모니터링 타입 안전성
"""

from typing import Any, TypedDict


class ExecutionTimeRange(TypedDict, total=False):
    """실행 시간 범위."""

    min: float
    max: float


class PerformanceAnalysis(TypedDict, total=False):
    """성능 분석 결과."""

    avg_execution_time: float
    success_rate: float
    total_runs: int
    performance_trend: str
    execution_time_range: ExecutionTimeRange
    error: str


class MonitoringAnalysis(TypedDict, total=False):
    """모니터링 분석 결과."""

    trace_id: str
    performance_analysis: PerformanceAnalysis
    learning_insights: list[str]
    recommendations: list[str]
    trinity_score: float
    monitoring_mode: str


class MentorInitStatus(TypedDict, total=False):
    """선생 초기화 상태."""

    status: str
    langsmith_available: bool
    obsidian_librarian_connected: bool
    project_name: str
    error: str


class LearningAssessment(TypedDict, total=False):
    """학습 평가."""

    baseline_trinity_score: float
    post_trinity_score: float
    improvement: float
    materials_effectiveness: bool
    execution_success: bool
    overall_grade: str


class LearningSessionData(TypedDict, total=False):
    """학습 세션 데이터."""

    topic: str
    timestamp: float
    materials: list[dict[str, Any]]
    baseline: MonitoringAnalysis
    execution: dict[str, Any]
    analysis: MonitoringAnalysis
    assessment: LearningAssessment


class LearningSessionResult(TypedDict, total=False):
    """학습 세션 결과."""

    session_id: str
    topic: str
    learning_materials: list[dict[str, Any]]
    execution_result: dict[str, Any]
    performance_analysis: MonitoringAnalysis
    learning_assessment: LearningAssessment
    recommendations: list[str]
    error: str


class MentorStatus(TypedDict, total=False):
    """선생 상태."""

    status: str
    langsmith_connected: bool
    obsidian_librarian_connected: bool
    active_learning_sessions: int
    project_name: str


class LearningHistory(TypedDict, total=False):
    """학습 히스토리."""

    total_sessions: int
    recent_sessions: list[str]
    session_details: dict[str, LearningSessionData]
