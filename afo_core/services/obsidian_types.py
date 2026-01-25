# Trinity Score: 95.0 (Obsidian Librarian Types)
"""
옵시디언 사서 시스템 TypedDict 정의
眞 (Truth): 정밀한 타입 계약
善 (Goodness): 지식 관리 타입 안전성
"""

from typing import TypedDict


class Document(TypedDict, total=False):
    """문서 정보."""

    id: str
    title: str
    content: str
    category: str
    keywords: list[str]
    tags: list[str]
    score: float


class DocumentList(TypedDict, total=False):
    """문서 목록."""

    items: list[Document]


class SearchResult(TypedDict, total=False):
    """검색 결과."""

    results: list[Document]


class GraphConnection(TypedDict):
    """그래프 연결."""

    target_id: str
    strength: float
    shared_keywords: list[str]


class GraphNode(TypedDict, total=False):
    """지식 그래프 노드."""

    type: str
    title: str
    category: str
    trinity_category: str
    keywords: list[str]
    tags: list[str]
    connections: list[GraphConnection]


class TrinityDistribution(TypedDict):
    """Trinity 분포."""

    truth: int
    goodness: int
    beauty: int
    serenity: int
    eternity: int


class LibrarianInitStatus(TypedDict, total=False):
    """사서 초기화 상태."""

    status: str
    total_documents: int
    trinity_distribution: TrinityDistribution
    knowledge_graph_nodes: int
    error: str


class LearningMaterialInfo(TypedDict, total=False):
    """학습 자료 정보."""

    id: str
    title: str
    trinity_category: str
    complexity_score: float
    priority_score: float
    relevance_score: float
    preview: str
    estimated_read_time: int
    prerequisites: list[str]
    learning_objectives: list[str]


class LearningPhase(TypedDict, total=False):
    """학습 단계."""

    phase: str
    trinity_focus: list[str]
    materials: list[LearningMaterialInfo]
    estimated_time: int


class LearningPathResult(TypedDict, total=False):
    """학습 경로 결과."""

    topic: str
    learner_level: str
    total_materials: int
    filtered_materials: int
    learning_path: list[LearningPhase]
    estimated_total_time: int
    trinity_distribution: TrinityDistribution
    error: str


class SessionExecutionResult(TypedDict, total=False):
    """세션 실행 결과."""

    success: bool
    steps_completed: int
    avg_success_rate: float


class SessionAssessment(TypedDict, total=False):
    """세션 평가."""

    overall_grade: str
    improvement: float


class PerformanceAnalysisData(TypedDict, total=False):
    """성능 분석 데이터."""

    avg_execution_time: float
    success_rate: float
    trinity_score: float


class SessionPerformance(TypedDict, total=False):
    """세션 성능."""

    trinity_score: float
    performance_analysis: PerformanceAnalysisData


class SessionData(TypedDict, total=False):
    """학습 세션 데이터."""

    topic: str
    trace_id: str
    materials_used: list[LearningMaterialInfo]
    execution_result: SessionExecutionResult
    performance_analysis: SessionPerformance
    assessment: SessionAssessment
    recommendations: list[str]


class RecordingResult(TypedDict, total=False):
    """기록 결과."""

    status: str
    file_path: str
    session_id: str
    error: str


class LibrarianStatus(TypedDict, total=False):
    """사서 상태."""

    status: str
    trinity_categories: dict[str, int]
    knowledge_graph_size: int
    obsidian_vault_path: str
    context7_integration: bool
