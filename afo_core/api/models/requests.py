# Trinity Score: 90.0 (Established by Chancellor)
"""AFO API Request Models
Phase 2 리팩토링: Request 모델 분리
"""

from pydantic import BaseModel, Field


class CommandRequest(BaseModel):
    """Command execution request"""

    command: str = Field(..., description="Command to execute")
    thread_id: str | None = Field(default=None, description="Thread ID for conversation")


class RAGQueryRequest(BaseModel):
    """RAG query request"""

    query: str = Field(..., description="Query string")
    llm_provider: str = Field(
        default="claude",
        description="LLM provider (claude, gemini, codex, ollama, lmstudio)",
    )
    expand_query: bool = Field(default=True, description="Use Query Expansion")
    expansion_method: str = Field(
        default="both", description="Expansion method (wordnet, embedding, both)"
    )


class YeongdeokCommandRequest(BaseModel):
    """Yeongdeok scholar command request"""

    command: str = Field(..., description="Command for Yeongdeok scholar")
    mode: str = Field(default="wet", description="Execution mode ('dry_run' or 'wet')")
    use_eyes: bool = Field(default=False, description="Use browser (eyes)")
    use_arms: bool = Field(default=False, description="Use n8n (arms)")
    url: str | None = Field(default=None, description="URL to view (when use_eyes=True)")


class BrowserClickRequest(BaseModel):
    """Browser click request"""

    x: int = Field(..., description="X coordinate (pixels)")
    y: int = Field(..., description="Y coordinate (pixels)")


class BrowserTypeRequest(BaseModel):
    """Browser type request"""

    text: str = Field(..., description="Text to type")


class BrowserKeyRequest(BaseModel):
    """Browser key press request"""

    key: str = Field(..., description="Key to press")


class BrowserScrollRequest(BaseModel):
    """Browser scroll request"""

    delta_y: int = Field(..., description="Scroll amount (positive: down, negative: up)")


class CrewAIExecuteRequest(BaseModel):
    """CrewAI execution request"""

    role: str = Field(..., description="Agent role (e.g., 'AI Researcher', 'Technical Writer')")
    goal: str = Field(..., description="Agent goal (e.g., 'Research latest AI trends')")
    backstory: str = Field(..., description="Agent backstory")
    task_description: str = Field(..., description="Task description")
    tools: list[str] | None = Field(
        default=[], description="Tools to use (e.g., ['search', 'db_query'])"
    )
    thread_id: str | None = Field(default=None, description="Conversation thread ID (optional)")


class LangChainToolsRequest(BaseModel):
    """LangChain tools request"""

    query: str = Field(..., description="Query string")
    tools: list[str] | None = Field(default=None, description="Tool names")


class LangChainRetrievalQARequest(BaseModel):
    """LangChain Retrieval QA request"""

    query: str = Field(..., description="User question")
    return_sources: bool = Field(default=True, description="Include source documents")
    confidence_threshold: float = Field(default=0.7, description="Confidence threshold (0.0-1.0)")
    model_name: str = Field(default="gpt-4", description="LLM model to use")
    use_local_embeddings: bool = Field(default=False, description="Use local embeddings")
