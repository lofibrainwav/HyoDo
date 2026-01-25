"""Multimodal Collaboration Models

협업 워크플로우 관련 데이터 모델들.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class CollaborationArtifact:
    """협업 아티팩트 데이터 클래스"""

    artifact_id: str
    artifact_type: str  # 'document', 'image', 'data', 'analysis', 'decision'
    content: Any
    metadata: dict[str, Any]
    created_by: str
    created_at: str
    parent_artifact_id: str | None = None
    version: int = 1
    tags: list[str] | None = None

    def __post_init__(self) -> None:
        if self.tags is None:
            self.tags = []


@dataclass
class WorkflowStep:
    """워크플로우 단계 데이터 클래스"""

    step_id: str
    step_name: str
    agent_responsible: str
    required_artifacts: list[str]
    produced_artifacts: list[str]
    status: str = "pending"  # 'pending', 'in_progress', 'completed', 'failed'
    started_at: str | None = None
    completed_at: str | None = None
    result: Any | None = None
    error_message: str | None = None


@dataclass
class CollaborationWorkflow:
    """협업 워크플로우 데이터 클래스"""

    workflow_id: str
    workflow_type: str  # 'tax_analysis', 'compliance_audit', 'strategic_planning'
    client_id: str
    session_id: str
    steps: list[WorkflowStep]
    artifacts: list[CollaborationArtifact]
    created_at: str
    updated_at: str
    status: str = "initialized"  # 'initialized', 'running', 'completed', 'failed'
    trinity_score_evolution: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.trinity_score_evolution is None:
            self.trinity_score_evolution = []
        if self.metadata is None:
            self.metadata = {}
