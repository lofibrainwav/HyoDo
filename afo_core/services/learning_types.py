# Trinity Score: 98.0 (Integrated Learning System Types)
"""
통합 학습 시스템 TypedDict 정의
眞 (Truth): 정밀한 타입 계약
善 (Goodness): 학습 시스템 타입 안전성
"""

from typing import Any, TypedDict


class LearnerConfig(TypedDict, total=False):
    """학습자 설정."""

    level: str  # "beginner" | "intermediate" | "advanced"
    focus_areas: list[str]  # ["truth", "goodness", "beauty"]


class LearningMaterial(TypedDict, total=False):
    """학습 자료."""

    title: str
    trinity_category: str
    source: str
    content: str


class LearningStep(TypedDict, total=False):
    """학습 단계."""

    phase: str
    materials: list[LearningMaterial]
    duration_estimate: int


class LearningPath(TypedDict, total=False):
    """학습 경로."""

    learning_path: list[LearningStep]
    topic: str
    estimated_duration: int


class PerformanceAnalysis(TypedDict, total=False):
    """성능 분석 결과."""

    success_rate: float
    latency_ms: float
    error_count: int
    recommendations: list[str]


class MonitoringResult(TypedDict, total=False):
    """모니터링 결과."""

    status: str
    trinity_score: float
    performance_analysis: PerformanceAnalysis
    recommendations: list[str]


class StepExecutionResult(TypedDict, total=False):
    """단계 실행 결과."""

    step_index: int
    step_name: str
    materials_count: int
    execution_result: dict[str, Any]
    success: bool
    error: str


class ComprehensiveAssessment(TypedDict, total=False):
    """종합 학습 평가."""

    baseline_trinity_score: float
    final_trinity_score: float
    trinity_improvement: float
    avg_step_success_rate: float
    materials_effective: bool
    execution_success: bool
    overall_success: bool
    overall_grade: str
    learning_strengths: list[str]
    learning_weaknesses: list[str]
    materials_utilization: int
    steps_completed: int
    assessment_timestamp: float


class LearningSessionResult(TypedDict, total=False):
    """학습 세션 결과."""

    session_id: str
    topic: str
    learner_config: LearnerConfig
    duration_seconds: float
    learning_path: LearningPath
    execution_results: list[StepExecutionResult]
    baseline_monitoring: MonitoringResult
    final_analysis: MonitoringResult
    comprehensive_assessment: ComprehensiveAssessment
    recommendations: list[str]
    next_learning_suggestions: list[str]
    error: str


class SessionData(TypedDict, total=False):
    """세션 데이터."""

    topic: str
    start_time: float
    end_time: float
    assessment: ComprehensiveAssessment
    final_result: LearningSessionResult


class SystemInitStatus(TypedDict, total=False):
    """시스템 초기화 상태."""

    status: str
    obsidian_librarian: dict[str, Any]
    langsmith_mentor: dict[str, Any]
    context7_connected: bool
    integration_level: str
    error: str


class SystemStatusResponse(TypedDict, total=False):
    """시스템 상태 응답."""

    system_status: str
    active_sessions: int
    obsidian_librarian: dict[str, Any]
    langsmith_mentor: dict[str, Any]
    context7_connected: bool
    integration_health: str
    error: str


class BestSessionInfo(TypedDict):
    """최고 세션 정보."""

    topic: str
    grade: str | None
    improvement: float


class LearningAnalytics(TypedDict, total=False):
    """학습 분석 데이터."""

    total_sessions: int
    avg_trinity_improvement: float
    avg_success_rate: float
    best_session: BestSessionInfo
    grade_distribution: dict[str, int]
    recent_topics: list[str]
    message: str
