# Trinity Score: 97.0 (Phase 30 Complete Multimodal RAG Refactoring)
"""
Multimodal RAG Engine - Backward Compatibility Wrapper

This file now serves as a backward compatibility wrapper for the refactored
multimodal_rag package. All functionality has been moved to the multimodal_rag/
directory for better organization and maintainability.

Original: 553 lines → Refactored: 6 files, 150-200 lines each
- multimodal_rag/documents.py - MultimodalDocument 클래스
- multimodal_rag/engine.py - MultimodalRAGEngine 클래스 (메인 로직)
- multimodal_rag/memory.py - 메모리 관리 기능
- multimodal_rag/services.py - Vision/Audio 서비스 통합
- multimodal_rag/utils.py - 헬퍼 함수들
- multimodal_rag/__init__.py - 패키지 초기화

Migration completed: 2026-01-16
"""

# Backward compatibility - import from refactored package
from multimodal_rag import (
    VERSION,
    MultimodalDocument,
    MultimodalRAGEngine,
    add_multimodal_content,
    get_engine_stats,
    get_multimodal_engine,
    search_multimodal,
)

# Re-export for backward compatibility
__all__ = [
    "MultimodalDocument",
    "MultimodalRAGEngine",
    "get_multimodal_engine",
    "VERSION",
    "add_multimodal_content",
    "get_engine_stats",
    "search_multimodal",
]
