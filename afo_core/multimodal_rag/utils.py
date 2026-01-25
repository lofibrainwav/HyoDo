# Trinity Score: 95.0 (Phase 30 Multimodal Utils Refactoring)
"""Multimodal RAG Utilities - Helper Functions and Global Instances"""

import logging
from typing import Any

from .engine import MultimodalRAGEngine

logger = logging.getLogger(__name__)

# Default instance
_multimodal_rag_engine = MultimodalRAGEngine()


def get_multimodal_engine() -> MultimodalRAGEngine:
    """Get the default multimodal RAG engine instance."""
    try:
        return _multimodal_rag_engine
    except (AttributeError, NameError) as e:
        logger.warning("기본 엔진 인스턴스 접근 실패, 새 인스턴스 생성: %s", str(e))
        return MultimodalRAGEngine()
    except Exception as e:
        logger.debug("엔진 인스턴스 접근 중 예상치 못한 에러: %s", str(e))
        return MultimodalRAGEngine()


def process_image_for_rag_legacy(image_path: str) -> dict[str, Any]:
    """Legacy image processing function (deprecated, use engine.add_image instead)."""
    logger.warning(
        "process_image_for_rag_legacy is deprecated. Use MultimodalRAGEngine.add_image() instead."
    )
    get_multimodal_engine()

    # This would need to be updated to match the new API
    # For now, return a basic result
    return {
        "path": image_path,
        "processed": False,
        "deprecated": True,
        "message": "Use MultimodalRAGEngine.add_image() instead",
    }


def get_engine_stats() -> dict[str, Any]:
    """Get comprehensive engine statistics."""
    engine = get_multimodal_engine()
    return engine.get_stats()


def search_multimodal(query: str, top_k: int = 5, **kwargs: Any) -> list[Any]:
    """Convenience function for multimodal search."""
    engine = get_multimodal_engine()
    return engine.search(query, top_k, **kwargs)


def add_multimodal_content(
    content: str, content_type: str = "text", metadata: dict[str, Any] | None = None
) -> bool:
    """Convenience function for adding content to the multimodal engine."""
    engine = get_multimodal_engine()
    return engine.add_document(content, content_type, metadata)
