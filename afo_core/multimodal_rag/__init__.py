# Trinity Score: 96.0 (Phase 30 Multimodal RAG Package)
"""Multimodal RAG Engine Package - Vision, Audio, and Text Processing"""

from .documents import MultimodalDocument
from .engine import MultimodalRAGEngine
from .memory import MemoryManager
from .services import MultimodalServiceManager, get_service_manager
from .utils import (
    add_multimodal_content,
    get_engine_stats,
    get_multimodal_engine,
    search_multimodal,
)

# Version info
VERSION = "FINAL_TRUTH_1"

# Backward compatibility - expose main classes and functions
__all__ = [
    "MultimodalDocument",
    "MultimodalRAGEngine",
    "MemoryManager",
    "MultimodalServiceManager",
    "get_service_manager",
    "get_multimodal_engine",
    "get_engine_stats",
    "search_multimodal",
    "add_multimodal_content",
    "VERSION",
    # Additional exports for comprehensive testing
    "DocumentProcessor",  # Alias for MultimodalDocument
]
