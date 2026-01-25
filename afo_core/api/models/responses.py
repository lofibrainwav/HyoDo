# Trinity Score: 90.0 (Established by Chancellor)
"""AFO API Response Models
Phase 2 리팩토링: Response 모델 분리
"""

from typing import Any

from pydantic import BaseModel, Field


class CrewAIExecuteResponse(BaseModel):
    """CrewAI execution response"""

    status: str = Field(..., description="Execution status ('success' or 'error')")
    result: str | None = Field(default=None, description="Execution result")
    agent_role: str | None = Field(default=None, description="Agent role")
    error: str | None = Field(default=None, description="Error message (if error)")


class MultimodalRAGResponse(BaseModel):
    """Multimodal RAG response"""

    answer: str = Field(..., description="Generated answer")
    text_results: list[dict[str, Any]] = Field(default=[], description="Text search results")
    image_results: list[dict[str, Any]] = Field(default=[], description="Image search results")
    reranked_results: list[dict[str, Any]] | None = Field(
        default=None, description="Reranking results (optional)"
    )
    metadata: dict[str, Any] | None = Field(default=None, description="Metadata")


class LangChainToolsResponse(BaseModel):
    """LangChain tools response"""

    status: str = Field(..., description="Execution status ('success' or 'error')")
    result: str | None = Field(default=None, description="Execution result")
    tools_used: list[str] | None = Field(default=[], description="Tools used")
    error: str | None = Field(default=None, description="Error message (if error)")


class LangChainRetrievalQAResponse(BaseModel):
    """LangChain Retrieval QA response"""

    question: str = Field(..., description="User question")
    answer: str = Field(..., description="Generated answer")
    confidence: dict[str, Any] = Field(
        ..., description="Confidence information (score, level, threshold)"
    )
    sources: list[dict[str, Any]] = Field(default=[], description="Source document information")
    metadata: dict[str, Any] = Field(..., description="Metadata (model, processing time, etc.)")
    warning: str | None = Field(default=None, description="Confidence warning message")
