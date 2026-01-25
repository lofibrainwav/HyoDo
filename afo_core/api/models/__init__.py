# Trinity Score: 90.0 (Established by Chancellor)
"""
AFO API Models
Phase 2 리팩토링: Request/Response 모델 분리
"""

from api.models.requests import (
    BrowserClickRequest,
    BrowserKeyRequest,
    BrowserScrollRequest,
    BrowserTypeRequest,
    CommandRequest,
    CrewAIExecuteRequest,
    LangChainRetrievalQARequest,
    LangChainToolsRequest,
    RAGQueryRequest,
    YeongdeokCommandRequest,
)

from .responses import (
    CrewAIExecuteResponse,
    LangChainRetrievalQAResponse,
    LangChainToolsResponse,
    MultimodalRAGResponse,
)

__all__ = [
    "BrowserClickRequest",
    "BrowserKeyRequest",
    "BrowserScrollRequest",
    "BrowserTypeRequest",
    "CommandRequest",
    "CrewAIExecuteRequest",
    "CrewAIExecuteResponse",
    "LangChainRetrievalQARequest",
    "LangChainRetrievalQAResponse",
    "LangChainToolsRequest",
    "LangChainToolsResponse",
    "MultimodalRAGResponse",
    "RAGQueryRequest",
    "YeongdeokCommandRequest",
]
